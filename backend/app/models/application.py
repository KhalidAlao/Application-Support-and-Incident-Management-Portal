from backend.extensions import db
from sqlalchemy import func
from backend.app.utils import utc_now
from backend.app.utils import CriticalityLevel

class Application(db.Model):
    __tablename__ = 'applications'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    criticality = db.Column(db.String(20), nullable=False, default=CriticalityLevel.MEDIUM.value)
    owner_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    is_active = db.Column(db.Boolean, nullable=False, default=True)

    created_at = db.Column(
        db.DateTime(timezone=True),
        server_default=func.now(),
        default=utc_now,
        nullable=False
    )
    updated_at = db.Column(
        db.DateTime(timezone=True),
        server_default=func.now(),
        default=utc_now,
        onupdate=utc_now,
        nullable=False
    )

    def __repr__(self):
        return f'<Application {self.name}>'