from backend.extensions import db
from sqlalchemy import func
from backend.app.utils import utc_now

class KnowledgeArticle(db.Model):
    __tablename__ = 'knowledge_articles'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    tags = db.Column(db.String(500), nullable=True)
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

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
    
    __table_args__ = (
    db.Index('idx_article_title', 'title'),
    db.Index('idx_article_created', 'created_at'),
)

    author = db.relationship('User', backref='knowledge_articles')
    incident_links = db.relationship('IncidentKnowledge', backref='article', lazy=True, cascade='all, delete-orphan')

    def __repr__(self):
        return f'<KnowledgeArticle {self.id}: {self.title[:30]}>'