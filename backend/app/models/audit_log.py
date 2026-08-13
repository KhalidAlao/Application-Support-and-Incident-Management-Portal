from backend.extensions import db
from sqlalchemy import func
from backend.app.utils import utc_now

class AuditLog(db.Model):
    __tablename__ = 'audit_logs'

    id = db.Column(db.Integer, primary_key=True)
    incident_id = db.Column(db.Integer, db.ForeignKey('incidents.id'), nullable=False)
    actor_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    actor_name = db.Column(db.String(100), nullable=False)
    field_changed = db.Column(db.String(50), nullable=False)
    old_value = db.Column(db.Text, nullable=True)
    new_value = db.Column(db.Text, nullable=True)
    reason = db.Column(db.Text, nullable=True)

    # Only one timestamp – no onupdate needed
    timestamp = db.Column(
        db.DateTime(timezone=True),
        server_default=func.now(),
        default=utc_now,
        nullable=False
    )

    __table_args__ = (
        db.Index('idx_audit_incident', 'incident_id'),
        db.Index('idx_audit_timestamp', 'timestamp'),
        db.Index('idx_audit_field', 'field_changed'),
    )

    def __repr__(self):
        return f'<AuditLog {self.id}: {self.field_changed} on incident {self.incident_id}>'