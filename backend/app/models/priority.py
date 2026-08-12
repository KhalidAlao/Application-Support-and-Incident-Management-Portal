from backend.extensions import db
from backend.app.utils import PriorityCode, ImpactLevel, UrgencyLevel

class Priority(db.Model):
    __tablename__ = 'priorities'

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(10), unique=True, nullable=False)
    label = db.Column(db.String(50), nullable=False)
    impact_level = db.Column(db.String(20), nullable=False)
    urgency_level = db.Column(db.String(20), nullable=False)
    response_minutes = db.Column(db.Integer, nullable=False)
    resolution_minutes = db.Column(db.Integer, nullable=False)

    # No timestamps needed for lookup table

    def __repr__(self):
        return f'<Priority {self.code}>'