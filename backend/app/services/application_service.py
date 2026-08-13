from typing import List, Optional, Dict, Any, Tuple
from backend.extensions import db
from backend.app.models import Application, User
from backend.app.utils.constants import Role, CriticalityLevel

class ApplicationService:
    """Service layer for Application CRUD with soft delete."""

    @staticmethod
    def get_applications(include_inactive: bool = False) -> List[Application]:
        """List applications, optionally including inactive ones."""
        query = Application.query
        if not include_inactive:
            query = query.filter(Application.is_active.is_(True))
        return query.order_by(Application.name).all()

    @staticmethod
    def get_application(app_id: int) -> Optional[Application]:
        """Fetch an application by ID (ignores active status)."""
        return db.session.get(Application, app_id)

    @staticmethod
    def create_application(data: Dict[str, Any], current_user: User) -> Application:
        """Create a new application. Only team_lead/admin."""
        if current_user.role not in [Role.TEAM_LEAD.value, Role.ADMIN.value]:
            raise PermissionError("Only team leads and admins can create applications")

        # Validate owner exists
        owner = db.session.get(User, data['owner_id'])
        if not owner:
            raise ValueError(f"User with id {data['owner_id']} does not exist")

        app = Application(
            name=data['name'],
            description=data.get('description'),
            criticality=data.get('criticality', CriticalityLevel.MEDIUM.value),
            owner_id=data['owner_id'],
            is_active=True,
        )
        db.session.add(app)
        db.session.commit()
        return app

    @staticmethod
    def update_application(app_id: int, data: Dict[str, Any], current_user: User) -> Tuple[Optional[Application], str]:
        """Update an application. Only team_lead/admin."""
        if current_user.role not in [Role.TEAM_LEAD.value, Role.ADMIN.value]:
            raise PermissionError("Only team leads and admins can update applications")

        app = db.session.get(Application, app_id)
        if not app:
            return None, "Application not found"

        # If owner_id is being updated, validate new owner exists
        if 'owner_id' in data:
            owner = db.session.get(User, data['owner_id'])
            if not owner:
                raise ValueError(f"User with id {data['owner_id']} does not exist")

        if 'name' in data:
            app.name = data['name']
        if 'description' in data:
            app.description = data['description']
        if 'criticality' in data:
            app.criticality = data['criticality']
        if 'owner_id' in data:
            app.owner_id = data['owner_id']

        db.session.commit()
        return app, "Updated"

    @staticmethod
    def deactivate_application(app_id: int, current_user: User) -> Tuple[bool, str]:
        """Soft-delete an application. Only team_lead/admin."""
        if current_user.role not in [Role.TEAM_LEAD.value, Role.ADMIN.value]:
            raise PermissionError("Only team leads and admins can deactivate applications")

        app = db.session.get(Application, app_id)
        if not app:
            return False, "Application not found"

        app.is_active = False
        db.session.commit()
        return True, "Application deactivated"

    @staticmethod
    def reactivate_application(app_id: int, current_user: User) -> Tuple[bool, str]:
        """Reactivate a soft-deleted application."""
        if current_user.role not in [Role.TEAM_LEAD.value, Role.ADMIN.value]:
            raise PermissionError("Only team leads and admins can reactivate applications")

        app = db.session.get(Application, app_id)
        if not app:
            return False, "Application not found"

        app.is_active = True
        db.session.commit()
        return True, "Application reactivated"