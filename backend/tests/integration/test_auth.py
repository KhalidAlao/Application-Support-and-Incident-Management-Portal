import pytest
from backend.app.services.auth_service import AuthService
from backend.app.models import User
from backend.extensions import db
from backend.tests.conftest import auth_headers


def test_login_success(client, admin_user_id):
    """Test successful login returns token and user info."""
    user = db.session.get(User, admin_user_id)

    response = client.post('/api/auth/login', json={
        'email': 'admin@example.com',
        'password': 'password'
    })

    assert response.status_code == 200
    data = response.get_json()
    assert 'access_token' in data
    assert 'user' in data
    assert data['user']['email'] == 'admin@example.com'
    assert data['user']['role'] == 'admin'
    assert data['expires_in'] == 3600


def test_login_support_success(client, support_user_id):
    """Test login with support engineer credentials."""
    user = db.session.get(User, support_user_id)

    response = client.post('/api/auth/login', json={
        'email': 'engineer@example.com',
        'password': 'password'
    })

    assert response.status_code == 200
    data = response.get_json()
    assert data['user']['role'] == 'support_engineer'


def test_login_invalid_email(client):
    """Test login with non-existent email returns 401."""
    response = client.post('/api/auth/login', json={
        'email': 'nonexistent@example.com',
        'password': 'password'
    })

    assert response.status_code == 401
    assert 'error' in response.get_json()


def test_login_invalid_password(client, admin_user_id):
    """Test login with wrong password returns 401."""
    user = db.session.get(User, admin_user_id)

    response = client.post('/api/auth/login', json={
        'email': 'admin@example.com',
        'password': 'wrongpassword'
    })

    assert response.status_code == 401
    assert 'error' in response.get_json()


def test_login_missing_email(client):
    """Test login with missing email returns 400."""
    response = client.post('/api/auth/login', json={
        'password': 'password'
    })

    assert response.status_code == 400
    assert 'errors' in response.get_json()


def test_login_missing_password(client):
    """Test login with missing password returns 400."""
    response = client.post('/api/auth/login', json={
        'email': 'admin@example.com'
    })

    assert response.status_code == 400
    assert 'errors' in response.get_json()