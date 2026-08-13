from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from collections import defaultdict
from backend.extensions import db
from backend.app.models import Incident, Application, Priority
from backend.app.utils.constants import IncidentStatus, OPEN_STATUSES


class IncidentRepository:
    """Centralized repository for complex/aggregate queries on Incidents."""

    @staticmethod
    def get_status_summary() -> Dict[str, Any]:
        """Returns counts by status, plus total_open and total_closed."""
        status_counts = {}
        results = db.session.query(
            Incident.status,
            db.func.count(Incident.id).label('count')
        ).group_by(Incident.status).all()
        for row in results:
            status_counts[row.status] = row.count

        total_open = db.session.query(db.func.count(Incident.id)).filter(
            Incident.status.in_(OPEN_STATUSES)
        ).scalar() or 0

        total_closed = db.session.query(db.func.count(Incident.id)).filter(
            Incident.status == IncidentStatus.CLOSED.value
        ).scalar() or 0

        return {
            'status_counts': status_counts,
            'total_open': total_open,
            'total_closed': total_closed,
        }

    @staticmethod
    def get_avg_resolution_time_by_priority() -> List[Dict[str, Any]]:
        """
        Average actual resolution time (minutes) grouped by priority.
        Computed in Python rather than database-side GROUP BY + AVG() to avoid
        SQLite/PostgreSQL dialect differences in date arithmetic (func.extract).
        This is a deliberate trade‑off:
            - Pros: portable across test (SQLite) and production (PostgreSQL),
                    simpler to test without environment-specific skips.
            - Cons: If the incidents table grows large (>10k rows), this
                    will become a performance bottleneck. At that point,
                    switch to a database‑side aggregate query using
                    func.extract('epoch', ...) and Postgres.
        """
        incidents = Incident.query.filter(
            Incident.resolved_at.isnot(None)
        ).all()

        groups = defaultdict(list)
        for inc in incidents:
            if inc.assigned_priority_id:
                groups[inc.assigned_priority_id].append((inc.created_at, inc.resolved_at))

        result = []
        for priority_id, pairs in groups.items():
            total_seconds = sum((res - cre).total_seconds() for cre, res in pairs)
            count = len(pairs)
            avg_minutes = (total_seconds / count) / 60 if count else None
            priority = db.session.get(Priority, priority_id)
            if priority:
                result.append({
                    'priority': priority.code,
                    'avg_resolution_minutes': round(avg_minutes, 1) if avg_minutes is not None else None
                })
        return result

    @staticmethod
    def get_stats_by_application() -> List[Dict[str, Any]]:
        """
        Incident count and average resolution time per application.
        Same trade‑off as get_avg_resolution_time_by_priority:
        computed in Python for portability across SQLite/PostgreSQL.
        """
        incidents = Incident.query.filter(
            Incident.resolved_at.isnot(None)
        ).all()

        groups = defaultdict(list)
        for inc in incidents:
            groups[inc.application_id].append((inc.created_at, inc.resolved_at))

        result = []
        for app_id, pairs in groups.items():
            count = len(pairs)
            total_seconds = sum((res - cre).total_seconds() for cre, res in pairs)
            avg_seconds = total_seconds / count if count else 0
            avg_minutes = avg_seconds / 60 if count else None
            app = db.session.get(Application, app_id)
            if app:
                result.append({
                    'application_id': app.id,
                    'application_name': app.name,
                    'incident_count': count,
                    'avg_resolution_minutes': round(avg_minutes, 1) if avg_minutes is not None else None,
                })
        return result

    @staticmethod
    def get_overdue_incidents(limit: int = 50) -> List[Incident]:
        """Incidents with resolve_due < now and still open."""
        now = datetime.now(timezone.utc)
        return Incident.query.filter(
            Incident.resolve_due.isnot(None),
            Incident.resolve_due < now,
            Incident.status.in_(OPEN_STATUSES)
        ).order_by(Incident.resolve_due.asc()).limit(limit).all()

    @staticmethod
    def get_overdue_count() -> int:
        """Return the count of overdue open incidents (resolve_due < now, not closed/resolved)."""
        now = datetime.now(timezone.utc)
        return db.session.query(db.func.count(Incident.id)).filter(
            Incident.resolve_due.isnot(None),
            Incident.resolve_due < now,
            Incident.status.in_(OPEN_STATUSES)
        ).scalar() or 0