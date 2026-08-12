import pytest
from backend.app import create_app
from backend.extensions import db as _db
from backend.config import TestingConfig
from backend.app.models import User
from backend.app.services.auth_service import AuthService
from backend.app.utils.constants import Role

@pytest.fixture
def app():
    app = create_app(TestingConfig)
    with app.app_context():
        _db.create_all()
        yield app
        _db.drop_all()

@pytest.fixture
def client(app):
    return app.test_client()

# Helper function to get auth headers for a user by ID
def auth_headers_for_user_id(user_id):
    """Generate authentication headers for a user by ID."""
    user = _db.session.get(User, user_id)
    token = AuthService.create_token(user)
    return {'Authorization': f'Bearer {token}'}

# Helper function to get auth headers for a User object (if attached)
def auth_headers(user):
    """Generate authentication headers for a given user."""
    token = AuthService.create_token(user)
    return {'Authorization': f'Bearer {token}'}

@pytest.fixture
def admin_user_id(app):
    """Seed an admin user and return its ID."""
    with app.app_context():
        user = User.query.filter_by(email='admin@example.com').first()
        if not user:
            hashed_password = AuthService.hash_password('password')
            user = User(
                name='Admin User',
                email='admin@example.com',
                hashed_password=hashed_password,
                role=Role.ADMIN.value
            )
            _db.session.add(user)
            _db.session.commit()
            _db.session.refresh(user)
        return user.id

@pytest.fixture
def support_user_id(app):
    """Seed a support engineer user and return its ID."""
    with app.app_context():
        user = User.query.filter_by(email='engineer@example.com').first()
        if not user:
            hashed_password = AuthService.hash_password('password')
            user = User(
                name='Support Engineer',
                email='engineer@example.com',
                hashed_password=hashed_password,
                role=Role.SUPPORT_ENGINEER.value
            )
            _db.session.add(user)
            _db.session.commit()
            _db.session.refresh(user)
        return user.id

@pytest.fixture
def reporter_user_id(app):
    """Seed a reporter user and return its ID."""
    with app.app_context():
        user = User.query.filter_by(email='reporter@example.com').first()
        if not user:
            hashed_password = AuthService.hash_password('password')
            user = User(
                name='Reporter User',
                email='reporter@example.com',
                hashed_password=hashed_password,
                role=Role.REPORTER.value
            )
            _db.session.add(user)
            _db.session.commit()
            _db.session.refresh(user)
        return user.id

@pytest.fixture
def team_lead_user_id(app):
    """Seed a team lead user and return its ID."""
    with app.app_context():
        user = User.query.filter_by(email='teamlead@example.com').first()
        if not user:
            hashed_password = AuthService.hash_password('password')
            user = User(
                name='Team Lead User',
                email='teamlead@example.com',
                hashed_password=hashed_password,
                role=Role.TEAM_LEAD.value
            )
            _db.session.add(user)
            _db.session.commit()
            _db.session.refresh(user)
        return user.id