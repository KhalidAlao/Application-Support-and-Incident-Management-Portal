from datetime import datetime, timedelta, timezone
import pytest
from backend.app.models import Incident, Priority, Application, User
from backend.app.utils import utc_now
from backend.extensions import db
from backend.tests.conftest import auth_headers
import backend.app.utils.datetime_utils  # for monkeypatching


def test_create_incident_success(client, reporter_user_id):
    """Test creating an incident as a reporter."""
    user = db.session.get(User, reporter_user_id)

    app_obj = Application.query.first()
    if not app_obj:
        app_obj = Application(
            name='Test App',
            description='Test application',
            criticality='medium',
            owner_id=user.id
        )
        db.session.add(app_obj)
        db.session.commit()

    response = client.post(
        '/api/incidents',
        json={
            'title': 'Test Incident',
            'description': 'This is a test incident',
            'reported_priority_text': 'This is urgent!',
            'application_id': app_obj.id
        },
        headers=auth_headers(user)
    )

    assert response.status_code == 201
    data = response.get_json()
    assert data['title'] == 'Test Incident'
    assert data['reporter_id'] == user.id
    assert data['status'] == 'new'
    assert data['impact'] is None
    assert data['urgency'] is None
    assert data['assigned_priority_id'] is None


def test_create_incident_no_auth(client):
    """Test creating an incident without authentication."""
    response = client.post('/api/incidents', json={
        'title': 'Test Incident',
        'description': 'This is a test incident',
        'application_id': 1
    })
    # The route exists but returns 401 (Unauthorized) without token
    assert response.status_code == 401


def test_create_incident_missing_fields(client, reporter_user_id):
    """Test creating an incident with missing required fields."""
    user = db.session.get(User, reporter_user_id)

    response = client.post(
        '/api/incidents',
        json={
            'title': 'Test Incident'
            # Missing description and application_id
        },
        headers=auth_headers(user)
    )
    assert response.status_code == 400
    assert 'errors' in response.get_json()


def test_list_incidents_as_reporter(client, reporter_user_id):
    """Test listing incidents as a reporter (should only see own)."""
    user = db.session.get(User, reporter_user_id)

    app_obj = Application.query.first()
    if not app_obj:
        app_obj = Application(
            name='Test App',
            description='Test application',
            criticality='medium',
            owner_id=user.id
        )
        db.session.add(app_obj)
        db.session.commit()

    for i in range(3):
        incident = Incident(
            title=f'Incident {i}',
            description='Test description',
            application_id=app_obj.id,
            reporter_id=user.id,
            status='new'
        )
        db.session.add(incident)
    db.session.commit()

    response = client.get(
        '/api/incidents',
        headers=auth_headers(user)
    )
    assert response.status_code == 200
    data = response.get_json()
    assert data['total'] >= 3
    for item in data['items']:
        assert item['reporter_id'] == user.id


def test_list_incidents_as_admin(client, admin_user_id):
    """Test listing incidents as admin (should see all)."""
    user = db.session.get(User, admin_user_id)

    response = client.get(
        '/api/incidents',
        headers=auth_headers(user)
    )
    assert response.status_code == 200
    data = response.get_json()
    assert 'items' in data


def test_get_incident_as_reporter_own(client, reporter_user_id):
    """Test getting own incident as reporter."""
    user = db.session.get(User, reporter_user_id)

    app_obj = Application.query.first()
    if not app_obj:
        app_obj = Application(
            name='Test App',
            description='Test application',
            criticality='medium',
            owner_id=user.id
        )
        db.session.add(app_obj)
        db.session.commit()

    incident = Incident(
        title='My Incident',
        description='Test',
        application_id=app_obj.id,
        reporter_id=user.id,
        status='new'
    )
    db.session.add(incident)
    db.session.commit()

    response = client.get(
        f'/api/incidents/{incident.id}',
        headers=auth_headers(user)
    )
    assert response.status_code == 200
    data = response.get_json()
    assert data['id'] == incident.id


def test_get_incident_as_reporter_other(client, reporter_user_id, admin_user_id):
    """Test reporter cannot see another user's incident."""
    reporter = db.session.get(User, reporter_user_id)
    admin = db.session.get(User, admin_user_id)

    app_obj = Application.query.first()
    if not app_obj:
        app_obj = Application(
            name='Test App',
            description='Test application',
            criticality='medium',
            owner_id=admin.id
        )
        db.session.add(app_obj)
        db.session.commit()

    incident = Incident(
        title='Admin Incident',
        description='Test',
        application_id=app_obj.id,
        reporter_id=admin.id,
        status='new'
    )
    db.session.add(incident)
    db.session.commit()

    response = client.get(
        f'/api/incidents/{incident.id}',
        headers=auth_headers(reporter)
    )
    assert response.status_code == 404


def test_triage_incident_as_support(client, support_user_id, reporter_user_id):
    """Test support engineer can triage an incident."""
    support = db.session.get(User, support_user_id)
    reporter = db.session.get(User, reporter_user_id)

    app_obj = Application.query.first()
    if not app_obj:
        app_obj = Application(
            name='Test App',
            description='Test application',
            criticality='medium',
            owner_id=reporter.id
        )
        db.session.add(app_obj)
        db.session.commit()

    incident = Incident(
        title='To Triage',
        description='Triage me',
        application_id=app_obj.id,
        reporter_id=reporter.id,
        status='new'
    )
    db.session.add(incident)
    db.session.commit()

    priority = Priority.query.filter_by(code='P1').first()
    if not priority:
        priority = Priority(
            code='P1',
            label='Critical',
            impact_level='high',
            urgency_level='high',
            response_minutes=60,
            resolution_minutes=240
        )
        db.session.add(priority)
        db.session.commit()

    response = client.post(
        f'/api/incidents/{incident.id}/triage',
        json={
            'impact': 'high',
            'urgency': 'high',
            'priority_code': 'P1'
        },
        headers=auth_headers(support)
    )

    assert response.status_code == 200
    data = response.get_json()
    assert data['impact'] == 'high'
    assert data['urgency'] == 'high'
    assert data['assigned_priority_id'] == priority.id
    assert data['status'] == 'triage'
    assert data['response_due'] is not None
    assert data['resolve_due'] is not None


def test_triage_incident_already_triaged_deny_support(client, support_user_id, reporter_user_id):
    """Test support engineer cannot re-triage an already triaged incident."""
    support = db.session.get(User, support_user_id)
    reporter = db.session.get(User, reporter_user_id)

    app_obj = Application.query.first()
    if not app_obj:
        app_obj = Application(
            name='Test App',
            description='Test application',
            criticality='medium',
            owner_id=reporter.id
        )
        db.session.add(app_obj)
        db.session.commit()

    priority = Priority.query.filter_by(code='P1').first()
    if not priority:
        priority = Priority(
            code='P1',
            label='Critical',
            impact_level='high',
            urgency_level='high',
            response_minutes=60,
            resolution_minutes=240
        )
        db.session.add(priority)
        db.session.commit()

    now = utc_now()
    incident = Incident(
        title='Already Triaged',
        description='Already has priority',
        application_id=app_obj.id,
        reporter_id=reporter.id,
        status='triage',
        impact='high',
        urgency='high',
        assigned_priority_id=priority.id,
        response_due=now,
        resolve_due=now + timedelta(hours=4)
    )
    db.session.add(incident)
    db.session.commit()

    response = client.post(
        f'/api/incidents/{incident.id}/triage',
        json={
            'impact': 'medium',
            'urgency': 'medium',
            'priority_code': 'P2'
        },
        headers=auth_headers(support)
    )

    assert response.status_code == 403
    data = response.get_json()
    assert 'Support engineers cannot change existing priority' in data['error']

def test_assign_incident_as_team_lead(client, team_lead_user_id, support_user_id, reporter_user_id):
    team_lead = db.session.get(User, team_lead_user_id)
    support = db.session.get(User, support_user_id)
    reporter = db.session.get(User, reporter_user_id)

    app_obj = Application.query.first()
    if not app_obj:
        app_obj = Application(name='Test App', description='test', criticality='medium', owner_id=reporter.id)
        db.session.add(app_obj)
        db.session.commit()

    incident = Incident(title='To Assign', description='test', application_id=app_obj.id, reporter_id=reporter.id, status='new')
    db.session.add(incident)
    db.session.commit()

    response = client.post(f'/api/incidents/{incident.id}/assign',
                           json={'assignee_id': support.id},
                           headers=auth_headers(team_lead))
    assert response.status_code == 200
    data = response.get_json()
    assert data['assignee_id'] == support.id
    assert data['status'] == 'assigned'  # auto-transition

def test_assign_incident_as_support_denied(client, support_user_id, reporter_user_id):
    support = db.session.get(User, support_user_id)
    reporter = db.session.get(User, reporter_user_id)
    app_obj = Application.query.first()
    if not app_obj:
        app_obj = Application(name='Test App', description='test', criticality='medium', owner_id=reporter.id)
        db.session.add(app_obj)
        db.session.commit()
    incident = Incident(title='Denied', description='test', application_id=app_obj.id, reporter_id=reporter.id, status='new')
    db.session.add(incident)
    db.session.commit()
    response = client.post(f'/api/incidents/{incident.id}/assign',
                           json={'assignee_id': 999},
                           headers=auth_headers(support))
    assert response.status_code == 403

def test_legal_status_transition(client, support_user_id, reporter_user_id):
    support = db.session.get(User, support_user_id)
    reporter = db.session.get(User, reporter_user_id)
    app_obj = Application.query.first()
    if not app_obj:
        app_obj = Application(name='Test App', description='test', criticality='medium', owner_id=reporter.id)
        db.session.add(app_obj)
        db.session.commit()
    # Create and triage (to have priority set)
    priority = Priority.query.filter_by(code='P1').first()
    if not priority:
        priority = Priority(code='P1', label='Critical', impact_level='high', urgency_level='high',
                            response_minutes=60, resolution_minutes=240)
        db.session.add(priority)
        db.session.commit()
    incident = Incident(title='Status Test', description='test', application_id=app_obj.id,
                        reporter_id=reporter.id, status='triage',
                        impact='high', urgency='high', assigned_priority_id=priority.id,
                        response_due=utc_now(), resolve_due=utc_now()+timedelta(hours=4))
    db.session.add(incident)
    db.session.commit()
    incident.assignee_id = support.id
    incident.status = 'assigned'
    db.session.commit()

    response = client.post(f'/api/incidents/{incident.id}/status',
                           json={'status': 'in_progress'},
                           headers=auth_headers(support))
    assert response.status_code == 200
    assert response.get_json()['status'] == 'in_progress'

def test_illegal_status_transition(client, support_user_id, reporter_user_id):
    support = db.session.get(User, support_user_id)
    reporter = db.session.get(User, reporter_user_id)
    app_obj = Application.query.first()
    if not app_obj:
        app_obj = Application(name='Test App', description='test', criticality='medium', owner_id=reporter.id)
        db.session.add(app_obj)
        db.session.commit()
    incident = Incident(title='Illegal', description='test', application_id=app_obj.id,
                        reporter_id=reporter.id, status='new')
    db.session.add(incident)
    db.session.commit()
    incident.assignee_id = support.id
    db.session.commit()

    response = client.post(f'/api/incidents/{incident.id}/status',
                           json={'status': 'resolved'},
                           headers=auth_headers(support))
    assert response.status_code == 400
    assert 'Illegal transition' in response.get_json()['error']

def test_closed_requires_resolution_code(client, support_user_id, team_lead_user_id, reporter_user_id):
    support = db.session.get(User, support_user_id)
    team_lead = db.session.get(User, team_lead_user_id)
    reporter = db.session.get(User, reporter_user_id)
    app_obj = Application.query.first()
    if not app_obj:
        app_obj = Application(name='Test App', description='test', criticality='medium', owner_id=reporter.id)
        db.session.add(app_obj)
        db.session.commit()
    priority = Priority.query.filter_by(code='P1').first()
    if not priority:
        priority = Priority(code='P1', label='Critical', impact_level='high', urgency_level='high',
                            response_minutes=60, resolution_minutes=240)
        db.session.add(priority)
        db.session.commit()
    incident = Incident(title='Close Test', description='test', application_id=app_obj.id,
                        reporter_id=reporter.id, status='resolved',
                        impact='high', urgency='high', assigned_priority_id=priority.id,
                        response_due=utc_now(), resolve_due=utc_now()+timedelta(hours=4))
    db.session.add(incident)
    db.session.commit()
    incident.assignee_id = support.id
    db.session.commit()

    # Try to close without resolution_code
    response = client.post(f'/api/incidents/{incident.id}/status',
                           json={'status': 'closed'},
                           headers=auth_headers(team_lead))  # team_lead is allowed to close
    assert response.status_code == 400
    assert 'Resolution code required' in response.get_json()['error']

    # Now with resolution_code
    response = client.post(f'/api/incidents/{incident.id}/status',
                           json={'status': 'closed', 'resolution_code': 'fixed'},
                           headers=auth_headers(team_lead))
    assert response.status_code == 200
    assert response.get_json()['status'] == 'closed'
    assert response.get_json()['resolution_code'] == 'fixed'

def test_hold_time_arithmetic(client, support_user_id, reporter_user_id, monkeypatch):
    support = db.session.get(User, support_user_id)
    reporter = db.session.get(User, reporter_user_id)
    app_obj = Application.query.first()
    if not app_obj:
        app_obj = Application(name='Test App', description='test', criticality='medium', owner_id=reporter.id)
        db.session.add(app_obj)
        db.session.commit()
    priority = Priority.query.filter_by(code='P1').first()
    if not priority:
        priority = Priority(code='P1', label='Critical', impact_level='high', urgency_level='high',
                            response_minutes=60, resolution_minutes=240)
        db.session.add(priority)
        db.session.commit()

    base_time = datetime(2026, 8, 13, 10, 0, tzinfo=timezone.utc)
    incident = Incident(
        title='Hold Test',
        description='test',
        application_id=app_obj.id,
        reporter_id=reporter.id,
        status='assigned',
        impact='high',
        urgency='high',
        assigned_priority_id=priority.id,
        response_due=base_time + timedelta(minutes=60),
        resolve_due=base_time + timedelta(minutes=240),
        total_hold_minutes=0,
        hold_started_at=None
    )
    db.session.add(incident)
    db.session.commit()
    incident.assignee_id = support.id
    db.session.commit()

    # Patch the service's `utc_now` directly
    def fake_now_60():
        return base_time + timedelta(minutes=60)
    monkeypatch.setattr('backend.app.services.incident_service.utc_now', fake_now_60)

    response = client.post(
        f'/api/incidents/{incident.id}/status',
        json={'status': 'on_hold'},
        headers=auth_headers(support)
    )
    assert response.status_code == 200
    data = response.get_json()
    assert data['status'] == 'on_hold'
    assert data['hold_started_at'] is not None

    def fake_now_180():
        return base_time + timedelta(minutes=180)
    monkeypatch.setattr('backend.app.services.incident_service.utc_now', fake_now_180)

    response = client.post(
        f'/api/incidents/{incident.id}/status',
        json={'status': 'in_progress'},
        headers=auth_headers(support)
    )
    assert response.status_code == 200
    data = response.get_json()
    assert data['status'] == 'in_progress'
    assert data['hold_started_at'] is None
    assert data['total_hold_minutes'] == 120

    expected_resolve = base_time + timedelta(minutes=360)
    returned_resolve = datetime.fromisoformat(data['resolve_due'].replace('Z', '+00:00'))
    if returned_resolve.tzinfo is None:
        returned_resolve = returned_resolve.replace(tzinfo=timezone.utc)
    assert returned_resolve == expected_resolve
    
def test_incident_response_includes_audit_logs(client, admin_user_id, support_user_id, reporter_user_id):
    """
    Verify that GET /incidents/:id returns an audit_logs key with a list of entries
    in chronological order (oldest first) after multiple mutations.
    """
    admin = db.session.get(User, admin_user_id)
    support = db.session.get(User, support_user_id)
    reporter = db.session.get(User, reporter_user_id)

    # Create an application
    app = Application(name='Audit Test App', description='test', criticality='medium', owner_id=admin.id)
    db.session.add(app)
    db.session.commit()

    # Create incident via API to trigger audit log creation
    response = client.post(
        '/api/incidents',
        json={
            'title': 'Audit Test Incident',
            'description': 'Initial description',
            'application_id': app.id
        },
        headers=auth_headers(reporter)
    )
    assert response.status_code == 201
    incident_data = response.get_json()
    incident_id = incident_data['id']

    # 2. Admin assigns the incident to support
    response = client.post(
        f'/api/incidents/{incident_id}/assign',
        json={'assignee_id': support.id},
        headers=auth_headers(admin)
    )
    assert response.status_code == 200

    # 3. Support changes status to in_progress
    response = client.post(
        f'/api/incidents/{incident_id}/status',
        json={'status': 'in_progress', 'reason': 'Working on it'},
        headers=auth_headers(support)
    )
    assert response.status_code == 200

    # 4. Support edits title
    response = client.put(
        f'/api/incidents/{incident_id}',
        json={'title': 'Audit Test Incident - Updated'},
        headers=auth_headers(support)
    )
    assert response.status_code == 200

    # Now fetch the incident as admin
    response = client.get(f'/api/incidents/{incident_id}', headers=auth_headers(admin))
    assert response.status_code == 200
    data = response.get_json()

    # Assert audit_logs exists and is a list
    assert 'audit_logs' in data
    logs = data['audit_logs']
    assert isinstance(logs, list)
    assert len(logs) >= 4  # at least created, assignee, status, title

    # Check chronological order (oldest first)
    timestamps = [log['timestamp'] for log in logs]
    from datetime import datetime
    dt_timestamps = [datetime.fromisoformat(ts.replace('Z', '+00:00')) for ts in timestamps]
    assert dt_timestamps == sorted(dt_timestamps)  # strictly increasing

    # Verify specific entries
    created_entry = next((l for l in logs if l['field_changed'] == 'created'), None)
    assert created_entry is not None
    assert 'Incident created by' in created_entry['new_value']

    assign_entry = next((l for l in logs if l['field_changed'] == 'assignee_id'), None)
    assert assign_entry is not None
    assert assign_entry['new_value'] == support.name

    status_entry = next((l for l in logs if l['field_changed'] == 'status' and l['new_value'] == 'in_progress'), None)
    assert status_entry is not None
    assert status_entry['old_value'] == 'assigned'  # assignment auto-transitioned from new to assigned

    title_entry = next((l for l in logs if l['field_changed'] == 'title'), None)
    assert title_entry is not None
    assert title_entry['old_value'] == 'Audit Test Incident'
    assert title_entry['new_value'] == 'Audit Test Incident - Updated'