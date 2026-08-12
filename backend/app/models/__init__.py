# Import models so Alembic/Flask-Migrate can detect them
from .user import User
from .priority import Priority
from .application import Application
from .incident import Incident
from .audit_log import AuditLog
from .knowledge_article import KnowledgeArticle
from .incident_knowledge import IncidentKnowledge

__all__ = [
    'User',
    'Priority',
    'Application',
    'Incident',
    'AuditLog',
    'KnowledgeArticle',
    'IncidentKnowledge',
]