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

@pytest.fixture
def admin_user(app):
    """Seed an admin user in the test database."""
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
        return user

@pytest.fixture
def support_user(app):
    """Seed a support engineer user in the test database."""
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
        return user

@pytest.fixture
def reporter_user(app):
    """Seed a reporter user in the test database."""
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
        return user

@pytest.fixture
def team_lead_user(app):
    """Seed a team lead user in the test database."""
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
        return user