from backend.extensions import db

class IncidentKnowledge(db.Model):
    __tablename__ = 'incident_knowledge'

    # Composite primary key – pure junction table, no extra attributes
    incident_id = db.Column(db.Integer, db.ForeignKey('incidents.id'), primary_key=True)
    knowledge_article_id = db.Column(db.Integer, db.ForeignKey('knowledge_articles.id'), primary_key=True)

    # No extra metadata – link audit is captured by AuditLog when engineer adds the link

    def __repr__(self):
        return f'<IncidentKnowledge {self.incident_id} - {self.knowledge_article_id}>'