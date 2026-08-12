from backend.extensions import db
from sqlalchemy import func, CheckConstraint
from backend.app.utils import IncidentStatus, ImpactLevel, UrgencyLevel, ResolutionCode

class Incident(db.Model):
    __tablename__ = 'incidents'

    id = db.Column(db.Integer, primary_key=True)

    # Core fields
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)

    # User's original priority description (free text)
    reported_priority_text = db.Column(db.String(255), nullable=True)

    # Impact and urgency chosen by support team
    impact = db.Column(db.String(20), nullable=False)
    urgency = db.Column(db.String(20), nullable=False)

    # Status (string, validated at service layer)
    status = db.Column(db.String(20), nullable=False, default=IncidentStatus.NEW.value, index=True)

    # SLA timestamps – nullable because priority may not be set yet
    response_due = db.Column(db.DateTime(timezone=True), nullable=True)
    resolve_due = db.Column(db.DateTime(timezone=True), nullable=True)

    # Hold tracking for SLA pausing
    total_hold_minutes = db.Column(db.Integer, nullable=False, default=0)
    hold_started_at = db.Column(db.DateTime(timezone=True), nullable=True)

    # Resolution tracking
    resolution_code = db.Column(db.String(30), nullable=True)

    # Timestamps
    created_at = db.Column(db.DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    updated_at = db.Column(
        db.DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )

    # Foreign Keys
    reporter_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    assignee_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True, index=True)
    application_id = db.Column(db.Integer, db.ForeignKey('applications.id'), nullable=False, index=True)
    assigned_priority_id = db.Column(db.Integer, db.ForeignKey('priorities.id'), nullable=True)

    # Check constraints (defense-in-depth)
    __table_args__ = (
        CheckConstraint(
            f"impact IN ('{ImpactLevel.LOW.value}', '{ImpactLevel.MEDIUM.value}', '{ImpactLevel.HIGH.value}')",
            name='valid_impact'
        ),
        CheckConstraint(
            f"urgency IN ('{UrgencyLevel.LOW.value}', '{UrgencyLevel.MEDIUM.value}', '{UrgencyLevel.HIGH.value}')",
            name='valid_urgency'
        ),
        CheckConstraint(
            f"status IN ('{IncidentStatus.NEW.value}', '{IncidentStatus.TRIAGE.value}', "
            f"'{IncidentStatus.ASSIGNED.value}', '{IncidentStatus.IN_PROGRESS.value}', "
            f"'{IncidentStatus.ON_HOLD.value}', '{IncidentStatus.RESOLVED.value}', "
            f"'{IncidentStatus.REOPENED.value}', '{IncidentStatus.CLOSED.value}')",
            name='valid_status'
        ),
        CheckConstraint(
            f"resolution_code IS NULL OR resolution_code IN ("
            f"'{ResolutionCode.FIXED.value}', '{ResolutionCode.WORKAROUND.value}', "
            f"'{ResolutionCode.NOT_A_BUG.value}', '{ResolutionCode.DUPLICATE.value}', "
            f"'{ResolutionCode.CANT_REPRODUCE.value}', '{ResolutionCode.THIRD_PARTY.value}')",
            name='valid_resolution_code'
        ),
        # Enforce: if priority is set, SLA deadlines must also be set
        CheckConstraint(
            '(assigned_priority_id IS NOT NULL AND response_due IS NOT NULL AND resolve_due IS NOT NULL) '
            'OR assigned_priority_id IS NULL',
            name='sla_requires_priority'
        ),
    )

    # Relationships
    reporter = db.relationship('User', foreign_keys=[reporter_id], backref='incidents_reported')
    assignee = db.relationship('User', foreign_keys=[assignee_id], backref='incidents_assigned')
    priority = db.relationship('Priority', foreign_keys=[assigned_priority_id], backref='incidents')
    application = db.relationship('Application', foreign_keys=[application_id], backref='incidents')

    # Audit logs – NO cascade (audit trail must survive incident deletion)
    audit_logs = db.relationship('AuditLog', backref='incident', lazy=True)

    # Knowledge links – cascade OK (junction table cleanup)
    knowledge_links = db.relationship('IncidentKnowledge', backref='incident', lazy=True, cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Incident {self.id}: {self.title[:30]}>'