import pytest
from datetime import datetime, timedelta, timezone
from backend.app.models import Incident, Priority, Application, User
from backend.extensions import db
from backend.tests.conftest import auth_headers


def test_summary_report(client, admin_user_id, reporter_user_id):
    admin = db.session.get(User, admin_user_id)
    reporter = db.session.get(User, reporter_user_id)

    app = Application(name='Report App', description='test', criticality='medium', owner_id=admin.id)
    db.session.add(app)
    db.session.commit()

    priority = Priority.query.filter_by(code='P1').first()
    if not priority:
        priority = Priority(code='P1', label='Critical', impact_level='high', urgency_level='high',
                            response_minutes=60, resolution_minutes=240)
        db.session.add(priority)
        db.session.commit()

    now = datetime.now(timezone.utc)

    inc1 = Incident(
        title='New',
        description='new',
        application_id=app.id,
        reporter_id=reporter.id,
        status='new'
        # no priority, so no response_due/resolve_due needed
    )

    inc2 = Incident(
        title='Resolved',
        description='resolved',
        application_id=app.id,
        reporter_id=reporter.id,
        status='resolved',
        resolved_at=now,
        assigned_priority_id=priority.id,
        response_due=now,          # satisfy CHECK constraint
        resolve_due=now,           # satisfy CHECK constraint
        created_at=now - timedelta(hours=2)
    )

    inc3 = Incident(
        title='Closed',
        description='closed',
        application_id=app.id,
        reporter_id=reporter.id,
        status='closed',
        resolved_at=now,
        assigned_priority_id=priority.id,
        response_due=now,          # satisfy CHECK constraint
        resolve_due=now,           # satisfy CHECK constraint
        created_at=now - timedelta(hours=3)
    )

    db.session.add_all([inc1, inc2, inc3])
    db.session.commit()

    response = client.get('/api/reports/summary', headers=auth_headers(admin))
    assert response.status_code == 200
    data = response.get_json()
    assert data['status_counts'].get('new') == 1
    assert data['status_counts'].get('resolved') == 1
    assert data['status_counts'].get('closed') == 1
    assert data['total_open'] >= 1
    assert data['total_closed'] >= 1


def test_avg_resolution_time_math(client, admin_user_id, reporter_user_id):
    admin = db.session.get(User, admin_user_id)
    reporter = db.session.get(User, reporter_user_id)

    app = Application(name='Report App 2', description='test', criticality='medium', owner_id=admin.id)
    db.session.add(app)
    db.session.commit()

    priority = Priority.query.filter_by(code='P1').first()
    if not priority:
        priority = Priority(code='P1', label='Critical', impact_level='high', urgency_level='high',
                            response_minutes=60, resolution_minutes=240)
        db.session.add(priority)
        db.session.commit()

    now = datetime.now(timezone.utc)

    inc1 = Incident(
        title='Resolved 1',
        description='test',
        application_id=app.id,
        reporter_id=reporter.id,
        status='resolved',
        resolved_at=now,
        assigned_priority_id=priority.id,
        response_due=now,          # satisfy CHECK constraint
        resolve_due=now,           # satisfy CHECK constraint
        created_at=now - timedelta(hours=2)   # 120 minutes
    )

    inc2 = Incident(
        title='Resolved 2',
        description='test',
        application_id=app.id,
        reporter_id=reporter.id,
        status='resolved',
        resolved_at=now,
        assigned_priority_id=priority.id,
        response_due=now,          # satisfy CHECK constraint
        resolve_due=now,           # satisfy CHECK constraint
        created_at=now - timedelta(hours=1)   # 60 minutes
    )

    db.session.add_all([inc1, inc2])
    db.session.commit()

    response = client.get('/api/reports/avg-resolution-time', headers=auth_headers(admin))
    assert response.status_code == 200
    data = response.get_json()

    # Find P1 entry
    for entry in data:
        if entry['priority'] == 'P1':
            # Average should be (120 + 60) / 2 = 90 minutes
            assert entry['avg_resolution_minutes'] == 90.0
            break


def test_reopened_clears_resolved_at(client, admin_user_id, support_user_id, reporter_user_id):
    """Test that resolved_at is cleared on reopen and set again on re-resolve."""
    admin = db.session.get(User, admin_user_id)
    support = db.session.get(User, support_user_id)
    reporter = db.session.get(User, reporter_user_id)

    app = Application(name='Report App 3', description='test', criticality='medium', owner_id=admin.id)
    db.session.add(app)
    db.session.commit()

    priority = Priority.query.filter_by(code='P1').first()
    if not priority:
        priority = Priority(code='P1', label='Critical', impact_level='high', urgency_level='high',
                            response_minutes=60, resolution_minutes=240)
        db.session.add(priority)
        db.session.commit()

    now = datetime.now(timezone.utc)

    # Create an incident that was resolved at T=0, then reopened, then re-resolved at T=120
    inc = Incident(
        title='Reopen Test',
        description='test',
        application_id=app.id,
        reporter_id=reporter.id,
        status='resolved',
        resolved_at=now - timedelta(hours=2),  # initial resolution
        assigned_priority_id=priority.id,
        created_at=now - timedelta(hours=4),
        response_due=now - timedelta(hours=3),  # satisfy CHECK constraint
        resolve_due=now - timedelta(hours=1),   # satisfy CHECK constraint
    )
    db.session.add(inc)
    db.session.commit()
    inc.assignee_id = support.id
    db.session.commit()

    # Reopen (should clear resolved_at)
    response = client.post(
        f'/api/incidents/{inc.id}/status',
        json={'status': 'reopened', 'reason': 'Customer says not fixed'},
        headers=auth_headers(support)
    )
    assert response.status_code == 200
    data = response.get_json()
    assert data['resolved_at'] is None
    assert data['status'] == 'reopened'

    # Transition to in_progress (legal from reopened)
    response = client.post(
        f'/api/incidents/{inc.id}/status',
        json={'status': 'in_progress'},
        headers=auth_headers(support)
    )
    assert response.status_code == 200

    # Resolve again
    response = client.post(
        f'/api/incidents/{inc.id}/status',
        json={'status': 'resolved'},
        headers=auth_headers(support)
    )
    assert response.status_code == 200
    data = response.get_json()
    # resolved_at should be set to now (utc_now)
    assert data['resolved_at'] is not None
    assert data['status'] == 'resolved'
    
def test_overdue_count(client, admin_user_id, reporter_user_id):
    admin = db.session.get(User, admin_user_id)
    reporter = db.session.get(User, reporter_user_id)

    app = Application(name='Overdue Test App', description='test', criticality='medium', owner_id=admin.id)
    db.session.add(app)
    db.session.commit()

    priority = Priority.query.filter_by(code='P1').first()
    if not priority:
        priority = Priority(code='P1', label='Critical', impact_level='high', urgency_level='high',
                            response_minutes=60, resolution_minutes=240)
        db.session.add(priority)
        db.session.commit()

    now = datetime.now(timezone.utc)

    # 1. Overdue open incident (should count)
    inc1 = Incident(
        title='Overdue Open',
        description='open and past resolve_due',
        application_id=app.id,
        reporter_id=reporter.id,
        status='assigned',
        assigned_priority_id=priority.id,
        resolve_due=now - timedelta(hours=2),
        response_due=now - timedelta(hours=1),
        created_at=now - timedelta(hours=3)
    )
    db.session.add(inc1)

    # 2. Overdue closed incident (should NOT count)
    inc2 = Incident(
        title='Overdue Closed',
        description='closed but past resolve_due',
        application_id=app.id,
        reporter_id=reporter.id,
        status='closed',
        assigned_priority_id=priority.id,
        resolve_due=now - timedelta(hours=2),
        response_due=now - timedelta(hours=1),
        created_at=now - timedelta(hours=3)
    )
    db.session.add(inc2)

    # 3. Overdue resolved incident (should NOT count)
    inc3 = Incident(
        title='Overdue Resolved',
        description='resolved but past resolve_due',
        application_id=app.id,
        reporter_id=reporter.id,
        status='resolved',
        assigned_priority_id=priority.id,
        resolve_due=now - timedelta(hours=2),
        response_due=now - timedelta(hours=1),
        created_at=now - timedelta(hours=3)
    )
    db.session.add(inc3)

    # 4. Open incident not overdue (should NOT count)
    inc4 = Incident(
        title='Open Not Overdue',
        description='open and future resolve_due',
        application_id=app.id,
        reporter_id=reporter.id,
        status='in_progress',
        assigned_priority_id=priority.id,
        resolve_due=now + timedelta(hours=4),
        response_due=now + timedelta(hours=2),
        created_at=now - timedelta(hours=1)
    )
    db.session.add(inc4)

    db.session.commit()

    # As admin, should see count = 1 (only inc1)
    response = client.get('/api/reports/overdue-count', headers=auth_headers(admin))
    assert response.status_code == 200
    data = response.get_json()
    assert data['count'] == 1

    # As reporter, should get 403
    response = client.get('/api/reports/overdue-count', headers=auth_headers(reporter))
    assert response.status_code == 403


def test_overdue_count_permission_denied_for_reporter(client, reporter_user_id):
    """Reporter cannot access overdue-count endpoint."""
    reporter = db.session.get(User, reporter_user_id)
    response = client.get('/api/reports/overdue-count', headers=auth_headers(reporter))
    assert response.status_code == 403