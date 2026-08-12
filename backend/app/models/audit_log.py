from backend.extensions import db
from sqlalchemy import func

class AuditLog(db.Model):
    __tablename__ = 'audit_logs'

    id = db.Column(db.Integer, primary_key=True)

    # Always scoped to an incident
    incident_id = db.Column(db.Integer, db.ForeignKey('incidents.id'), nullable=False)

    # Actor: nullable for system actions (auto-close, etc.)
    actor_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)

    # Snapshot of actor name at write time (always present, even for system)
    actor_name = db.Column(db.String(100), nullable=False)

    # What changed
    field_changed = db.Column(db.String(50), nullable=False)
    old_value = db.Column(db.Text, nullable=True)
    new_value = db.Column(db.Text, nullable=True)

    # Reason is optional at schema level; service layer enforces when required
    reason = db.Column(db.Text, nullable=True)

    # Timestamp with server default
    timestamp = db.Column(db.DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Indexes for common audit queries
    __table_args__ = (
        db.Index('idx_audit_incident', 'incident_id'),
        db.Index('idx_audit_timestamp', 'timestamp'),
        db.Index('idx_audit_field', 'field_changed'),
    )

    # Relationship back to Incident
    # incident = db.relationship('Incident', backref='audit_logs')

    def __repr__(self):
        return f'<AuditLog {self.id}: {self.field_changed} on incident {self.incident_id}>'