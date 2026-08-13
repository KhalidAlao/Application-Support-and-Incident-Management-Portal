import pytest
from backend.app.models import User
from backend.extensions import db
from backend.tests.conftest import auth_headers


def test_users_list_as_admin(client, admin_user_id, support_user_id, team_lead_user_id):
    """Admin should get list of assignable users (exclude reporters)."""
    admin = db.session.get(User, admin_user_id)
    # Requesting support_user_id and team_lead_user_id as fixtures
    # ensures those users are created in this test's isolated DB.
    # We don't need to use them directly.

    response = client.get('/api/users', headers=auth_headers(admin))
    assert response.status_code == 200
    data = response.get_json()

    assert isinstance(data, list)

    # No reporter users should be included
    for item in data:
        assert 'email' not in item
        assert item['role'] != 'reporter'
        assert 'id' in item
        assert 'name' in item
        assert 'role' in item

    # Check that our seeded engineer and teamlead are present
    roles = [item['role'] for item in data]
    assert 'admin' in roles
    assert 'support_engineer' in roles
    assert 'team_lead' in roles

    # Ensure the reporter is absent
    reporter_ids = [u.id for u in User.query.filter_by(role='reporter').all()]
    response_ids = [item['id'] for item in data]
    for r_id in reporter_ids:
        assert r_id not in response_ids


def test_users_list_as_support(client, support_user_id, admin_user_id, team_lead_user_id):
    """Support engineer should get the same list as admin."""
    support = db.session.get(User, support_user_id)
    # Request other fixtures to ensure they exist, even if unused

    response = client.get('/api/users', headers=auth_headers(support))
    assert response.status_code == 200
    data = response.get_json()

    assert isinstance(data, list)
    for item in data:
        assert 'email' not in item
        assert item['role'] != 'reporter'

    roles = [item['role'] for item in data]
    assert 'admin' in roles
    assert 'support_engineer' in roles
    assert 'team_lead' in roles


def test_users_list_as_reporter_denied(client, reporter_user_id):
    """Reporter should get 403 (insufficient permissions)."""
    reporter = db.session.get(User, reporter_user_id)

    response = client.get('/api/users', headers=auth_headers(reporter))
    assert response.status_code == 403