from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime, timedelta, timezone
from sqlalchemy import and_, or_, desc
from backend.extensions import db
from backend.app.models import Incident, User, Priority, Application, AuditLog
from backend.app.utils import calculate_sla_deadlines, IncidentStatus, utc_now, ensure_utc
from backend.app.utils.constants import Role, is_transition_legal, get_allowed_roles_for_transition


class IncidentService:
    """Service layer for incident operations with atomic audit logging."""

    @staticmethod
    def create_incident(data: Dict[str, Any], current_user: User) -> Incident:
        """Create a new incident with initial audit log entry."""
        incident = Incident(
            title=data['title'],
            description=data['description'],
            reported_priority_text=data.get('reported_priority_text'),
            application_id=data['application_id'],
            reporter_id=current_user.id,
            status=IncidentStatus.NEW.value,
            impact=None,
            urgency=None,
            assigned_priority_id=None,
            response_due=None,
            resolve_due=None,
            total_hold_minutes=0,
            hold_started_at=None,
        )

        db.session.add(incident)
        db.session.flush()

        audit = AuditLog(
            incident_id=incident.id,
            actor_id=current_user.id,
            actor_name=current_user.name,
            field_changed='created',
            old_value=None,
            new_value=f"Incident created by {current_user.name}",
            reason=None,
            timestamp=utc_now(),
        )
        db.session.add(audit)
        db.session.commit()

        return incident

    @staticmethod
    def get_incidents(
        current_user: User,
        status: Optional[str] = None,
        application_id: Optional[int] = None,
        assignee_id: Optional[int] = None,
        created_after: Optional[datetime] = None,
        created_before: Optional[datetime] = None,
        page: int = 1,
        per_page: int = 20
    ) -> tuple[List[Incident], int, int, int]:
        """Get incidents with role-aware filtering and pagination."""
        query = Incident.query

        if current_user.role == Role.REPORTER.value:
            query = query.filter(Incident.reporter_id == current_user.id)

        if status:
            query = query.filter(Incident.status == status)
        if application_id:
            query = query.filter(Incident.application_id == application_id)
        if assignee_id:
            query = query.filter(Incident.assignee_id == assignee_id)
        if created_after:
            query = query.filter(Incident.created_at >= created_after)
        if created_before:
            query = query.filter(Incident.created_at <= created_before)

        query = query.order_by(desc(Incident.created_at))

        total = query.count()
        items = query.offset((page - 1) * per_page).limit(per_page).all()
        pages = (total + per_page - 1) // per_page if total > 0 else 1

        return items, total, page, pages

    @staticmethod
    def get_incident(incident_id: int, current_user: User) -> Optional[Incident]:
        """Get a single incident with access control."""
        incident = db.session.get(Incident, incident_id)
        if not incident:
            return None

        if current_user.role == Role.REPORTER.value and incident.reporter_id != current_user.id:
            return None

        return incident

    @staticmethod
    def can_edit_incident(incident: Incident, current_user: User) -> Tuple[bool, str]:
        """Three-way permission check for editing an incident."""
        if current_user.role == Role.ADMIN.value:
            return True, ""
        if current_user.role == Role.TEAM_LEAD.value:
            return True, ""
        if current_user.role == Role.SUPPORT_ENGINEER.value and incident.assignee_id == current_user.id:
            return True, ""
        if (current_user.role == Role.REPORTER.value and 
            incident.reporter_id == current_user.id and 
            incident.status in [IncidentStatus.NEW.value, IncidentStatus.TRIAGE.value]):
            return True, ""
        return False, "Insufficient permissions"

    @staticmethod
    def update_incident(
        incident_id: int,
        data: Dict[str, Any],
        current_user: User
    ) -> Tuple[Optional[Incident], int, str]:
        """Update incident fields with audit logging."""
        incident = db.session.get(Incident, incident_id)
        if not incident:
            return None, 404, "Incident not found"

        is_allowed, reason = IncidentService.can_edit_incident(incident, current_user)
        if not is_allowed:
            return None, 403, reason

        changes = []
        if 'title' in data and data['title'] != incident.title:
            changes.append(('title', incident.title, data['title']))
            incident.title = data['title']
        if 'description' in data and data['description'] != incident.description:
            changes.append(('description', incident.description, data['description']))
            incident.description = data['description']

        if not changes:
            return incident, 200, "No changes"

        for field, old_val, new_val in changes:
            audit = AuditLog(
                incident_id=incident.id,
                actor_id=current_user.id,
                actor_name=current_user.name,
                field_changed=field,
                old_value=str(old_val) if old_val else None,
                new_value=str(new_val) if new_val else None,
                reason=None,
                timestamp=utc_now(),
            )
            db.session.add(audit)

        db.session.commit()
        return incident, 200, "Updated successfully"

    @staticmethod
    def triage_incident(
        incident_id: int,
        impact: str,
        urgency: str,
        priority_code: str,
        current_user: User
    ) -> Tuple[Optional[Incident], int, str]:
        """Triage an incident: set impact, urgency, priority, and SLA deadlines."""
        incident = db.session.get(Incident, incident_id)
        if not incident:
            return None, 404, "Incident not found"

        if current_user.role not in [Role.SUPPORT_ENGINEER.value, Role.TEAM_LEAD.value, Role.ADMIN.value]:
            return None, 403, "Insufficient permissions"

        if incident.assigned_priority_id is not None and current_user.role == Role.SUPPORT_ENGINEER.value:
            return None, 403, "Support engineers cannot change existing priority. Only team leads or admins can."

        priority = Priority.query.filter_by(code=priority_code).first()
        if not priority:
            return None, 400, f"Invalid priority code: {priority_code}"

        old_impact = incident.impact
        old_urgency = incident.urgency
        old_priority_id = incident.assigned_priority_id

        incident.impact = impact
        incident.urgency = urgency
        incident.assigned_priority_id = priority.id

        # NOTE: If the incident accumulated hold time before being triaged,
        # this calculation does not account for that hold time.
        # That is a known deferred edge case – we do not adjust for it now.
        start_time = utc_now()
        response_due, resolve_due = calculate_sla_deadlines(
            priority.response_minutes,
            priority.resolution_minutes,
            start_time
        )
        incident.response_due = response_due
        incident.resolve_due = resolve_due

        if incident.status == IncidentStatus.NEW.value:
            incident.status = IncidentStatus.TRIAGE.value

        if old_impact != impact:
            audit = AuditLog(
                incident_id=incident.id,
                actor_id=current_user.id,
                actor_name=current_user.name,
                field_changed='impact',
                old_value=old_impact,
                new_value=impact,
                reason='Triage',
                timestamp=utc_now(),
            )
            db.session.add(audit)

        if old_urgency != urgency:
            audit = AuditLog(
                incident_id=incident.id,
                actor_id=current_user.id,
                actor_name=current_user.name,
                field_changed='urgency',
                old_value=old_urgency,
                new_value=urgency,
                reason='Triage',
                timestamp=utc_now(),
            )
            db.session.add(audit)

        if old_priority_id != priority.id:
            audit = AuditLog(
                incident_id=incident.id,
                actor_id=current_user.id,
                actor_name=current_user.name,
                field_changed='assigned_priority_id',
                old_value=str(old_priority_id) if old_priority_id else None,
                new_value=str(priority.id),
                reason='Triage',
                timestamp=utc_now(),
            )
            db.session.add(audit)

        audit = AuditLog(
            incident_id=incident.id,
            actor_id=current_user.id,
            actor_name=current_user.name,
            field_changed='sla_deadlines',
            old_value=None,
            new_value=f"Response: {response_due.isoformat() if response_due else None}, Resolution: {resolve_due.isoformat() if resolve_due else None}",
            reason='Triage',
            timestamp=utc_now(),
        )
        db.session.add(audit)

        db.session.commit()
        return incident, 200, "Triage complete"

    @staticmethod
    def assign_incident(
        incident_id: int,
        assignee_id: int,
        current_user: User
    ) -> Tuple[Optional[Incident], int, str]:
        incident = db.session.get(Incident, incident_id)
        if not incident:
            return None, 404, "Incident not found"

        if current_user.role not in [Role.TEAM_LEAD.value, Role.ADMIN.value]:
            return None, 403, "Only team leads and admins can assign incidents"

        assignee = db.session.get(User, assignee_id)
        if not assignee:
            return None, 404, "Assignee user not found"

        old_assignee_id = incident.assignee_id
        old_assignee_name = None
        if old_assignee_id:
            old_user = db.session.get(User, old_assignee_id)
            old_assignee_name = old_user.name if old_user else None

        incident.assignee_id = assignee_id

        old_status = incident.status
        if old_status in [IncidentStatus.NEW.value, IncidentStatus.TRIAGE.value]:
            incident.status = IncidentStatus.ASSIGNED.value

        audit = AuditLog(
            incident_id=incident.id,
            actor_id=current_user.id,
            actor_name=current_user.name,
            field_changed='assignee_id',
            old_value=old_assignee_name or "Unassigned",
            new_value=assignee.name,
            reason=f"Assigned by {current_user.name}",
            timestamp=utc_now(),
        )
        db.session.add(audit)

        if old_status != incident.status:
            audit = AuditLog(
                incident_id=incident.id,
                actor_id=current_user.id,
                actor_name=current_user.name,
                field_changed='status',
                old_value=old_status,
                new_value=incident.status,
                reason=f"Auto‑transitioned to {incident.status} on assignment",
                timestamp=utc_now(),
            )
            db.session.add(audit)

        db.session.commit()
        return incident, 200, "Incident assigned successfully"

    @staticmethod
    def update_status(
        incident_id: int,
        new_status: str,
        current_user: User,
        reason: Optional[str] = None,
        resolution_code: Optional[str] = None
    ) -> Tuple[Optional[Incident], int, str]:
        incident = db.session.get(Incident, incident_id)
        if not incident:
            return None, 404, "Incident not found"

        old_status = incident.status

        # 1. Check legal transition (state machine)
        if not is_transition_legal(old_status, new_status):
            return None, 400, f"Illegal transition: {old_status} -> {new_status}"

        # 2. Role restriction – fail‐closed if no entry
        allowed_roles = get_allowed_roles_for_transition(old_status, new_status)
        if current_user.role not in allowed_roles:
            return None, 403, f"Insufficient permissions for {old_status} -> {new_status}"

        # 3. For support_engineer, must be assigned to this incident
        if current_user.role == Role.SUPPORT_ENGINEER.value and incident.assignee_id != current_user.id:
            return None, 403, "Support engineers can only update assigned incidents"

        # 4. Resolution code required for CLOSED
        if new_status == IncidentStatus.CLOSED.value and not resolution_code:
            return None, 400, "Resolution code required when closing an incident"

        # 5. Hold‑time bookkeeping (atomic)
        if new_status == IncidentStatus.ON_HOLD.value and old_status != IncidentStatus.ON_HOLD.value:
            # Entering hold: record start time
            incident.hold_started_at = utc_now()

        elif old_status == IncidentStatus.ON_HOLD.value and new_status != IncidentStatus.ON_HOLD.value:
            # Exiting hold: accumulate hold time and extend deadlines (if they exist)
            if incident.hold_started_at:
                now = utc_now()
                held_start = ensure_utc(incident.hold_started_at)
                held_seconds = (now - held_start).total_seconds()
                held_minutes = int(held_seconds // 60)
                if held_minutes > 0:
                    incident.total_hold_minutes += held_minutes
                    # Defensive guard: only extend deadlines if they exist
                    if incident.response_due is not None and incident.resolve_due is not None:
                        incident.response_due += timedelta(minutes=held_minutes)
                        incident.resolve_due += timedelta(minutes=held_minutes)
                    else:
                        # No SLA deadlines set (e.g., incident was never triaged).
                        # Record hold time but skip deadline extension; log for visibility.
                        audit = AuditLog(
                            incident_id=incident.id,
                            actor_id=current_user.id,
                            actor_name=current_user.name,
                            field_changed='hold_skipped',
                            old_value=None,
                            new_value=f"Hold time {held_minutes}min recorded but no SLA deadlines to extend",
                            reason="Incident left ON_HOLD without SLA deadlines set",
                            timestamp=utc_now(),
                        )
                        db.session.add(audit)
                incident.hold_started_at = None

        # 6. Apply status change
        incident.status = new_status

        # 7. Update resolved_at based on status transition
        if new_status in [IncidentStatus.RESOLVED.value, IncidentStatus.CLOSED.value]:
            incident.resolved_at = utc_now()
        elif new_status == IncidentStatus.REOPENED.value:
            incident.resolved_at = None

        # 8. Store resolution code if closed
        if new_status == IncidentStatus.CLOSED.value:
            incident.resolution_code = resolution_code

        # 9. Audit log
        audit = AuditLog(
            incident_id=incident.id,
            actor_id=current_user.id,
            actor_name=current_user.name,
            field_changed='status',
            old_value=old_status,
            new_value=new_status,
            reason=reason,
            timestamp=utc_now(),
        )
        db.session.add(audit)

        db.session.commit()
        return incident, 200, "Status updated successfully"