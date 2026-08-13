import click
from flask.cli import with_appcontext
from datetime import timedelta
from backend.extensions import db
from backend.app.models import User, Priority, Application, Incident
from backend.app.services.auth_service import AuthService
from backend.app.utils import (
    Role,
    PriorityCode,
    ImpactLevel,
    UrgencyLevel,
    CriticalityLevel,
    IncidentStatus,
    utc_now,
    calculate_sla_deadlines,
)


@click.command('seed-db')
@with_appcontext
def seed_db():
    """Seed the database with demo users, priorities, applications, and sample incidents."""
    click.echo("🌱 Seeding database...")

    # 1. Seed Users (idempotent by email)
    users_data = [
        {
            'name': 'Admin User',
            'email': 'admin@example.com',
            'password': 'password',
            'role': Role.ADMIN.value,
        },
        {
            'name': 'Support Engineer',
            'email': 'engineer@example.com',
            'password': 'password',
            'role': Role.SUPPORT_ENGINEER.value,
        },
        {
            'name': 'Team Lead',
            'email': 'teamlead@example.com',
            'password': 'password',
            'role': Role.TEAM_LEAD.value,
        },
        {
            'name': 'Reporter User',
            'email': 'reporter@example.com',
            'password': 'password',
            'role': Role.REPORTER.value,
        },
    ]

    created_users = {}
    for data in users_data:
        user = User.query.filter_by(email=data['email']).first()
        if not user:
            hashed = AuthService.hash_password(data['password'])
            user = User(
                name=data['name'],
                email=data['email'],
                hashed_password=hashed,
                role=data['role'],
            )
            db.session.add(user)
            db.session.flush()  # get id
            click.echo(f"  ✅ Created user: {data['email']}")
        else:
            click.echo(f"  ⏭️ User already exists: {data['email']}")
        created_users[data['email']] = user

    # 2. Seed Priorities (idempotent by code)
    priorities_data = [
        {
            'code': PriorityCode.P1.value,
            'label': 'Critical',
            'impact_level': ImpactLevel.HIGH.value,
            'urgency_level': UrgencyLevel.HIGH.value,
            'response_minutes': 60,
            'resolution_minutes': 240,
        },
        {
            'code': PriorityCode.P2.value,
            'label': 'High',
            'impact_level': ImpactLevel.HIGH.value,
            'urgency_level': UrgencyLevel.MEDIUM.value,
            'response_minutes': 120,
            'resolution_minutes': 480,
        },
        {
            'code': PriorityCode.P3.value,
            'label': 'Medium',
            'impact_level': ImpactLevel.MEDIUM.value,
            'urgency_level': UrgencyLevel.MEDIUM.value,
            'response_minutes': 240,
            'resolution_minutes': 1440,
        },
        {
            'code': PriorityCode.P4.value,
            'label': 'Low',
            'impact_level': ImpactLevel.LOW.value,
            'urgency_level': UrgencyLevel.LOW.value,
            'response_minutes': 480,
            'resolution_minutes': 2880,
        },
    ]

    priority_map = {}
    for data in priorities_data:
        priority = Priority.query.filter_by(code=data['code']).first()
        if not priority:
            priority = Priority(**data)
            db.session.add(priority)
            db.session.flush()
            click.echo(f"  ✅ Created priority: {data['code']}")
        else:
            click.echo(f"  ⏭️ Priority already exists: {data['code']}")
        priority_map[data['code']] = priority

    # 3. Seed Applications (idempotent by name)
    admin = created_users.get('admin@example.com')
    if not admin:
        admin = User.query.filter_by(email='admin@example.com').first()
        if not admin:
            click.echo("  ❌ Admin user not found; skipping applications.")
            return

    applications_data = [
        {
            'name': 'Council Portal',
            'description': 'Main resident portal for council services',
            'criticality': CriticalityLevel.HIGH.value,
            'owner_id': admin.id,
        },
        {
            'name': 'Internal HR System',
            'description': 'Staff leave, payroll, and HR records',
            'criticality': CriticalityLevel.MEDIUM.value,
            'owner_id': admin.id,
        },
    ]

    app_map = {}
    for data in applications_data:
        app = Application.query.filter_by(name=data['name']).first()
        if not app:
            app = Application(**data)
            db.session.add(app)
            db.session.flush()
            click.echo(f"  ✅ Created application: {data['name']}")
        else:
            click.echo(f"  ⏭️ Application already exists: {data['name']}")
        app_map[data['name']] = app

    # 4. Seed sample Incidents
    # Check if any of our specific sample incidents already exist (by title + description)
    # If they exist, skip creation to avoid duplicates.
    sample_titles = [
        'Cannot log in to Council Portal',
        'Payroll system showing incorrect leave balances',
        'API response times are slow',
        'Password reset email not arriving',
    ]
    existing_sample_count = Incident.query.filter(
        Incident.title.in_(sample_titles)
    ).count()

    if existing_sample_count == 0:
        p1 = priority_map.get(PriorityCode.P1.value)
        p3 = priority_map.get(PriorityCode.P3.value)
        app_council = app_map.get('Council Portal')
        app_hr = app_map.get('Internal HR System')
        reporter = created_users.get('reporter@example.com')
        engineer = created_users.get('engineer@example.com')

        if reporter and app_council and p1:
            now = utc_now()

            # 1. NEW incident – no priority, no SLA deadlines
            inc1 = Incident(
                title='Cannot log in to Council Portal',
                description='Users are reporting that they cannot log in to the Council Portal. Error message says "Invalid credentials" even with correct passwords.',
                application_id=app_council.id,
                reporter_id=reporter.id,
                status=IncidentStatus.NEW.value,
                impact=None,
                urgency=None,
                assigned_priority_id=None,
                response_due=None,
                resolve_due=None,
            )
            db.session.add(inc1)

            # 2. TRIAGE incident – priority set, compute SLA deadlines
            response_due, resolve_due = calculate_sla_deadlines(
                p1.response_minutes,
                p1.resolution_minutes,
                now
            )
            inc2 = Incident(
                title='Payroll system showing incorrect leave balances',
                description='Several staff members report that their annual leave balances are showing incorrect numbers. This affects HR approvals.',
                application_id=app_hr.id,
                reporter_id=reporter.id,
                status=IncidentStatus.TRIAGE.value,
                impact=ImpactLevel.HIGH.value,
                urgency=UrgencyLevel.HIGH.value,
                assigned_priority_id=p1.id,
                response_due=response_due,
                resolve_due=resolve_due,
            )
            db.session.add(inc2)

            # 3. ASSIGNED incident – priority set, compute SLA deadlines
            response_due, resolve_due = calculate_sla_deadlines(
                p3.response_minutes,
                p3.resolution_minutes,
                now
            )
            inc3 = Incident(
                title='API response times are slow',
                description='External API calls from the portal are taking >5 seconds, causing timeouts for users.',
                application_id=app_council.id,
                reporter_id=reporter.id,
                status=IncidentStatus.ASSIGNED.value,
                impact=ImpactLevel.MEDIUM.value,
                urgency=UrgencyLevel.MEDIUM.value,
                assigned_priority_id=p3.id,
                assignee_id=engineer.id if engineer else None,
                response_due=response_due,
                resolve_due=resolve_due,
            )
            db.session.add(inc3)

            # 4. RESOLVED incident – priority set, compute SLA deadlines, backdate created_at and resolved_at
            # Backdate by 3 hours to simulate realistic resolution time
            created_at = now - timedelta(hours=3)
            resolved_at = now
            # Compute deadlines based on creation time (not current time)
            response_due, resolve_due = calculate_sla_deadlines(
                p3.response_minutes,
                p3.resolution_minutes,
                created_at
            )
            inc4 = Incident(
                title='Password reset email not arriving',
                description='Users requesting password resets are not receiving the email. SPF/DKIM issue suspected.',
                application_id=app_council.id,
                reporter_id=reporter.id,
                status=IncidentStatus.RESOLVED.value,
                impact=ImpactLevel.MEDIUM.value,
                urgency=UrgencyLevel.MEDIUM.value,
                assigned_priority_id=p3.id,
                assignee_id=engineer.id if engineer else None,
                response_due=response_due,
                resolve_due=resolve_due,
                resolved_at=resolved_at,
                created_at=created_at,
            )
            db.session.add(inc4)

            click.echo("  ✅ Created 4 sample incidents.")
        else:
            click.echo("  ⚠️ Missing dependencies for sample incidents (reporter, app, priority). Skipping.")
    else:
        click.echo("  ⏭️ Sample incidents already exist; skipping.")

    # Commit all changes at once
    db.session.commit()
    click.echo("✅ Database seeding complete.")