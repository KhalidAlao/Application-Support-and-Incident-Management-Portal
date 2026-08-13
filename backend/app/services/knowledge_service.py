from typing import List, Optional, Tuple, Dict, Any
from backend.extensions import db
from backend.app.models import KnowledgeArticle, Incident, IncidentKnowledge, User, AuditLog
from backend.app.utils import utc_now
from backend.app.utils.constants import Role


class KnowledgeArticleService:
    """Service layer for Knowledge Articles with linking to incidents."""

    @staticmethod
    def create_article(data: Dict[str, Any], current_user: User) -> KnowledgeArticle:
        if current_user.role not in [Role.SUPPORT_ENGINEER.value, Role.TEAM_LEAD.value, Role.ADMIN.value]:
            raise PermissionError("Only support staff can create knowledge articles")

        article = KnowledgeArticle(
            title=data['title'],
            content=data['content'],
            tags=data.get('tags'),
            author_id=current_user.id,
        )
        db.session.add(article)
        db.session.commit()
        return article

    @staticmethod
    def get_article(article_id: int) -> Optional[KnowledgeArticle]:
        return db.session.get(KnowledgeArticle, article_id)

    @staticmethod
    def list_articles() -> List[KnowledgeArticle]:
        return KnowledgeArticle.query.order_by(KnowledgeArticle.title).all()

    @staticmethod
    def search_articles(query: str) -> List[KnowledgeArticle]:
        if not query:
            return KnowledgeArticleService.list_articles()
        search = f"%{query}%"
        return KnowledgeArticle.query.filter(
            db.or_(
                KnowledgeArticle.title.ilike(search),
                KnowledgeArticle.content.ilike(search),
                KnowledgeArticle.tags.ilike(search)
            )
        ).order_by(KnowledgeArticle.title).all()

    @staticmethod
    def update_article(article_id: int, data: Dict[str, Any], current_user: User) -> Tuple[Optional[KnowledgeArticle], str]:
        if current_user.role not in [Role.SUPPORT_ENGINEER.value, Role.TEAM_LEAD.value, Role.ADMIN.value]:
            raise PermissionError("Only support staff can update knowledge articles")

        article = db.session.get(KnowledgeArticle, article_id)
        if not article:
            return None, "Article not found"

        if 'title' in data:
            article.title = data['title']
        if 'content' in data:
            article.content = data['content']
        if 'tags' in data:
            article.tags = data['tags']

        db.session.commit()
        return article, "Updated"

    @staticmethod
    def delete_article(article_id: int, current_user: User) -> Tuple[bool, str]:
        if current_user.role not in [Role.SUPPORT_ENGINEER.value, Role.TEAM_LEAD.value, Role.ADMIN.value]:
            raise PermissionError("Only support staff can delete knowledge articles")

        article = db.session.get(KnowledgeArticle, article_id)
        if not article:
            return False, "Article not found"

        db.session.delete(article)
        db.session.commit()
        return True, "Article deleted"

    @staticmethod
    def link_to_incident(article_id: int, incident_id: int, current_user: User) -> Tuple[bool, str]:
        if current_user.role not in [Role.SUPPORT_ENGINEER.value, Role.TEAM_LEAD.value, Role.ADMIN.value]:
            raise PermissionError("Only support staff can link knowledge articles to incidents")

        article = db.session.get(KnowledgeArticle, article_id)
        if not article:
            return False, "Article not found"
        incident = db.session.get(Incident, incident_id)
        if not incident:
            return False, "Incident not found"

        # Check if already linked
        existing = IncidentKnowledge.query.filter_by(
            incident_id=incident_id, knowledge_article_id=article_id
        ).first()
        if existing:
            return False, "Article already linked to this incident"

        link = IncidentKnowledge(incident_id=incident_id, knowledge_article_id=article_id)
        db.session.add(link)

        # Audit log on the incident
        audit = AuditLog(
            incident_id=incident.id,
            actor_id=current_user.id,
            actor_name=current_user.name,
            field_changed='knowledge_linked',
            old_value=None,
            new_value=f"Linked article '{article.title}' (ID: {article.id})",
            reason=f"Linked by {current_user.name}",
            timestamp=utc_now(),
        )
        db.session.add(audit)

        db.session.commit()
        return True, "Article linked"

    @staticmethod
    def unlink_from_incident(article_id: int, incident_id: int, current_user: User) -> Tuple[bool, str]:
        if current_user.role not in [Role.SUPPORT_ENGINEER.value, Role.TEAM_LEAD.value, Role.ADMIN.value]:
            raise PermissionError("Only support staff can unlink knowledge articles")

        link = IncidentKnowledge.query.filter_by(
            incident_id=incident_id, knowledge_article_id=article_id
        ).first()
        if not link:
            return False, "Article not linked to this incident"

        article = db.session.get(KnowledgeArticle, article_id)
        incident = db.session.get(Incident, incident_id)

        db.session.delete(link)

        # Audit log on the incident
        if incident and article:
            audit = AuditLog(
                incident_id=incident.id,
                actor_id=current_user.id,
                actor_name=current_user.name,
                field_changed='knowledge_unlinked',
                old_value=f"Linked article '{article.title}' (ID: {article.id})",
                new_value=None,
                reason=f"Unlinked by {current_user.name}",
                timestamp=utc_now(),
            )
            db.session.add(audit)

        db.session.commit()
        return True, "Article unlinked"