import pytest
from backend.app.models import Application, User, Incident
from backend.extensions import db
from backend.tests.conftest import auth_headers


def test_create_application_as_team_lead(client, team_lead_user_id):
    team_lead = db.session.get(User, team_lead_user_id)
    response = client.post(
        '/api/applications',
        json={
            'name': 'TeamLead App',
            'description': 'Created by team lead',
            'criticality': 'high',
            'owner_id': team_lead.id,
        },
        headers=auth_headers(team_lead)
    )
    assert response.status_code == 201
    data = response.get_json()
    assert data['name'] == 'TeamLead App'
    assert data['owner_id'] == team_lead.id
    assert data['is_active'] is True


def test_create_application_as_support_denied(client, support_user_id):
    support = db.session.get(User, support_user_id)
    response = client.post(
        '/api/applications',
        json={
            'name': 'Denied App',
            'criticality': 'medium',
            'owner_id': support.id,
        },
        headers=auth_headers(support)
    )
    assert response.status_code == 403


def test_list_applications_excludes_inactive(client, admin_user_id):
    admin = db.session.get(User, admin_user_id)
    # Create an active app
    active = Application(name='Active App', description='active', criticality='low', owner_id=admin.id, is_active=True)
    # Create an inactive app
    inactive = Application(name='Inactive App', description='inactive', criticality='low', owner_id=admin.id, is_active=False)
    db.session.add_all([active, inactive])
    db.session.commit()

    response = client.get('/api/applications', headers=auth_headers(admin))
    assert response.status_code == 200
    data = response.get_json()
    names = [app['name'] for app in data]
    assert 'Active App' in names
    assert 'Inactive App' not in names

    # include_inactive=true
    response = client.get('/api/applications?include_inactive=true', headers=auth_headers(admin))
    data = response.get_json()
    names = [app['name'] for app in data]
    assert 'Active App' in names
    assert 'Inactive App' in names


def test_soft_delete_application(client, admin_user_id):
    admin = db.session.get(User, admin_user_id)
    app = Application(name='To Delete', description='will be soft-deleted', criticality='low', owner_id=admin.id, is_active=True)
    db.session.add(app)
    db.session.commit()

    response = client.delete(f'/api/applications/{app.id}', headers=auth_headers(admin))
    assert response.status_code == 200
    assert response.get_json()['message'] == 'Application deactivated'

    # Fetch directly should show is_active=False
    response = client.get(f'/api/applications/{app.id}', headers=auth_headers(admin))
    assert response.status_code == 200
    assert response.get_json()['is_active'] is False

    # Default list should exclude it
    response = client.get('/api/applications', headers=auth_headers(admin))
    assert app.id not in [a['id'] for a in response.get_json()]

    # Reactivate
    response = client.post(f'/api/applications/{app.id}/reactivate', headers=auth_headers(admin))
    assert response.status_code == 200
    assert response.get_json()['message'] == 'Application reactivated'

    # Now it appears in default list
    response = client.get('/api/applications', headers=auth_headers(admin))
    assert app.id in [a['id'] for a in response.get_json()]


def test_incident_references_soft_deleted_app(client, admin_user_id, reporter_user_id):
    admin = db.session.get(User, admin_user_id)
    reporter = db.session.get(User, reporter_user_id)

    # Create an application
    app = Application(name='App for Incident', description='will be deactivated', criticality='medium', owner_id=admin.id, is_active=True)
    db.session.add(app)
    db.session.commit()

    # Create an incident referencing the app
    incident = Incident(
        title='Incident with app',
        description='test',
        application_id=app.id,
        reporter_id=reporter.id,
        status='new'
    )
    db.session.add(incident)
    db.session.commit()

    # Soft-delete the app
    client.delete(f'/api/applications/{app.id}', headers=auth_headers(admin))

    # GET the incident – should still return with the application data (is_active=False)
    response = client.get(f'/api/incidents/{incident.id}', headers=auth_headers(admin))
    assert response.status_code == 200
    data = response.get_json()
    assert 'application' in data
    assert data['application']['id'] == app.id
    assert data['application']['name'] == 'App for Incident'

    # Also confirm the incident list still works
    response = client.get('/api/incidents', headers=auth_headers(admin))
    assert response.status_code == 200
    items = response.get_json()['items']
    # Should include the incident
    assert any(item['id'] == incident.id for item in items)

def test_create_application_invalid_owner(client, team_lead_user_id):
    team_lead = db.session.get(User, team_lead_user_id)
    response = client.post(
        '/api/applications',
        json={
            'name': 'Invalid Owner App',
            'criticality': 'medium',
            'owner_id': 99999,  # non-existent user
        },
        headers=auth_headers(team_lead)
    )
    assert response.status_code == 404
    assert 'does not exist' in response.get_json()['error']

def test_update_application_not_found(client, team_lead_user_id):
    """Attempt to update a non‑existent application returns 404."""
    team_lead = db.session.get(User, team_lead_user_id)
    response = client.put(
        '/api/applications/99999',
        json={'name': 'Does Not Exist'},
        headers=auth_headers(team_lead)
    )
    assert response.status_code == 404
    assert response.get_json()['error'] == 'Application not found'


def test_reactivate_application_not_found(client, admin_user_id):
    """Attempt to reactivate a non‑existent application returns 404."""
    admin = db.session.get(User, admin_user_id)
    response = client.post(
        '/api/applications/99999/reactivate',
        headers=auth_headers(admin)
    )
    assert response.status_code == 404
    assert response.get_json()['error'] == 'Application not found'
def test_update_application_success(client, team_lead_user_id):
    team_lead = db.session.get(User, team_lead_user_id)
    # Create an application
    response = client.post(
        '/api/applications',
        json={
            'name': 'Update Success',
            'criticality': 'medium',
            'owner_id': team_lead.id,
        },
        headers=auth_headers(team_lead)
    )
    assert response.status_code == 201
    app = response.get_json()

    # Update criticality
    update_response = client.put(
        f'/api/applications/{app["id"]}',
        json={'criticality': 'high'},
        headers=auth_headers(team_lead)
    )
    assert update_response.status_code == 200
    data = update_response.get_json()
    assert data['criticality'] == 'high'
    assert data['name'] == 'Update Success'  # unchanged

    # Fetch and confirm persistence
    get_response = client.get(f'/api/applications/{app["id"]}', headers=auth_headers(team_lead))
    assert get_response.status_code == 200
    assert get_response.get_json()['criticality'] == 'high'


def test_update_application_permission_denied(client, support_user_id, admin_user_id):
    admin = db.session.get(User, admin_user_id)
    response = client.post(
        '/api/applications',
        json={
            'name': 'Update Denied',
            'criticality': 'medium',
            'owner_id': admin.id,
        },
        headers=auth_headers(admin)
    )
    assert response.status_code == 201
    app = response.get_json()

    support = db.session.get(User, support_user_id)
    update_response = client.put(
        f'/api/applications/{app["id"]}',
        json={'criticality': 'high'},
        headers=auth_headers(support)
    )
    assert update_response.status_code == 403
    # The decorator returns this generic message, not the service-specific one
    assert 'Insufficient permissions' in update_response.get_json()['error']


def test_reactivate_application_success(client, admin_user_id):
    admin = db.session.get(User, admin_user_id)
    # Create app
    response = client.post(
        '/api/applications',
        json={
            'name': 'Reactivate Success',
            'criticality': 'low',
            'owner_id': admin.id,
        },
        headers=auth_headers(admin)
    )
    assert response.status_code == 201
    app = response.get_json()

    # Soft delete
    delete_response = client.delete(
        f'/api/applications/{app["id"]}',
        headers=auth_headers(admin)
    )
    assert delete_response.status_code == 200

    # Confirm is_active False
    get_response = client.get(f'/api/applications/{app["id"]}', headers=auth_headers(admin))
    assert get_response.status_code == 200
    assert get_response.get_json()['is_active'] is False

    # Reactivate
    reactivate_response = client.post(
        f'/api/applications/{app["id"]}/reactivate',
        headers=auth_headers(admin)
    )
    assert reactivate_response.status_code == 200
    assert reactivate_response.get_json()['message'] == 'Application reactivated'

    # Confirm is_active True
    get_response = client.get(f'/api/applications/{app["id"]}', headers=auth_headers(admin))
    assert get_response.status_code == 200
    assert get_response.get_json()['is_active'] is True

    # Confirm it appears in default list
    list_response = client.get('/api/applications', headers=auth_headers(admin))
    assert list_response.status_code == 200
    ids = [app['id'] for app in list_response.get_json()]
    assert app['id'] in ids


def test_reactivate_application_permission_denied(client, support_user_id, admin_user_id):
    admin = db.session.get(User, admin_user_id)
    response = client.post(
        '/api/applications',
        json={
            'name': 'Reactivate Denied',
            'criticality': 'low',
            'owner_id': admin.id,
        },
        headers=auth_headers(admin)
    )
    assert response.status_code == 201
    app = response.get_json()

    client.delete(f'/api/applications/{app["id"]}', headers=auth_headers(admin))

    support = db.session.get(User, support_user_id)
    reactivate_response = client.post(
        f'/api/applications/{app["id"]}/reactivate',
        headers=auth_headers(support)
    )
    assert reactivate_response.status_code == 403
    assert 'Insufficient permissions' in reactivate_response.get_json()['error']