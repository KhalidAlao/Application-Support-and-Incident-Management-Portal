from backend.extensions import db
from sqlalchemy import func
from backend.app.utils import CriticalityLevel, utc_now

class Application(db.Model):
    __tablename__ = 'applications'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    criticality = db.Column(db.String(20), nullable=False, default=CriticalityLevel.MEDIUM.value)

    # owner_id is NOT NULL – every application must have an accountable owner
    owner_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    # Timezone-aware UTC timestamps with database-level defaults
    created_at = db.Column(db.DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = db.Column(
        db.DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )

    def __repr__(self):
        return f'<Application {self.name}>'