from backend.extensions import db
from sqlalchemy import func, CheckConstraint
from backend.app.utils import utc_now
from backend.app.utils import IncidentStatus, ImpactLevel, UrgencyLevel, ResolutionCode

class Incident(db.Model):
    __tablename__ = 'incidents'

    id = db.Column(db.Integer, primary_key=True)

    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    reported_priority_text = db.Column(db.String(255), nullable=True)

    impact = db.Column(db.String(20), nullable=True)
    urgency = db.Column(db.String(20), nullable=True)

    status = db.Column(db.String(20), nullable=False, default=IncidentStatus.NEW.value, index=True)

    response_due = db.Column(db.DateTime(timezone=True), nullable=True)
    resolve_due = db.Column(db.DateTime(timezone=True), nullable=True)

    total_hold_minutes = db.Column(db.Integer, nullable=False, default=0)
    hold_started_at = db.Column(db.DateTime(timezone=True), nullable=True)

    resolution_code = db.Column(db.String(30), nullable=True)

    created_at = db.Column(
        db.DateTime(timezone=True),
        server_default=func.now(),
        default=utc_now,
        nullable=False,
        index=True
    )
    updated_at = db.Column(
        db.DateTime(timezone=True),
        server_default=func.now(),
        default=utc_now,
        onupdate=utc_now,
        nullable=False
    )

    # Foreign keys
    reporter_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    assignee_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True, index=True)
    application_id = db.Column(db.Integer, db.ForeignKey('applications.id'), nullable=False, index=True)
    assigned_priority_id = db.Column(db.Integer, db.ForeignKey('priorities.id'), nullable=True)

    resolved_at = db.Column(db.DateTime(timezone=True), nullable=True, index=True)

    # Check constraints (defense-in-depth)
    __table_args__ = (
        CheckConstraint(
            f"impact IS NULL OR impact IN ('{ImpactLevel.LOW.value}', '{ImpactLevel.MEDIUM.value}', '{ImpactLevel.HIGH.value}')",
            name='valid_impact'
        ),
        CheckConstraint(
            f"urgency IS NULL OR urgency IN ('{UrgencyLevel.LOW.value}', '{UrgencyLevel.MEDIUM.value}', '{UrgencyLevel.HIGH.value}')",
            name='valid_urgency'
        ),
        # ... other constraints
    )

    # Relationships
    reporter = db.relationship('User', foreign_keys=[reporter_id], backref='incidents_reported')
    assignee = db.relationship('User', foreign_keys=[assignee_id], backref='incidents_assigned')
    priority = db.relationship('Priority', foreign_keys=[assigned_priority_id], backref='incidents')
    application = db.relationship('Application', foreign_keys=[application_id], backref='incidents')
    audit_logs = db.relationship('AuditLog', backref='incident', lazy=True)
    knowledge_articles = db.relationship(
        'KnowledgeArticle',
        secondary='incident_knowledge',
        backref='incidents',
        lazy='select',
        viewonly=True
    )

    def __repr__(self):
        return f'<Incident {self.id}: {self.title[:30]}>'