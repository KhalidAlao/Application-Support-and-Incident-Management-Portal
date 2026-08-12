from backend.extensions import db
from sqlalchemy import func

class KnowledgeArticle(db.Model):
    __tablename__ = 'knowledge_articles'

    id = db.Column(db.Integer, primary_key=True)

    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)

    # Tags stored as delimited string (comma-separated)
    # Example: "database,performance,troubleshooting"
    tags = db.Column(db.String(500), nullable=True)

    # Author
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    # Timestamps
    created_at = db.Column(db.DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = db.Column(
        db.DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )

    # Indexes for search
    __table_args__ = (
        db.Index('idx_article_title', 'title'),
        db.Index('idx_article_created', 'created_at'),
    )

    # Relationships
    author = db.relationship('User', foreign_keys=[author_id], backref='knowledge_articles')

    # Junction table relationship (defined later)
    # incident_links = db.relationship('IncidentKnowledge', backref='article', lazy=True)

    def __repr__(self):
        return f'<KnowledgeArticle {self.id}: {self.title[:30]}>'