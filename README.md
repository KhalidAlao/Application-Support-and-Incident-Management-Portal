# Application Support and Incident Management Portal

A full-stack incident management system built for a support/service-desk workflow: ticket creation, triage, assignment, SLA tracking, knowledge base, and reporting — with role-based access control and a complete, immutable audit trail on every incident.

Built as a structured learning project, developed phase-by-phase from domain modeling through deployment, with an emphasis on verifying every change against real Postgres data rather than assumptions.

## Live Demo
   
   Deployed on Render: https://application-support-and-incident.onrender.com
   
   Demo credentials:
   - admin@example.com / password

## Tech Stack

**Backend:** Python 3.9, Flask (application factory pattern), SQLAlchemy, Alembic (via Flask-Migrate), Flask-JWT-Extended, Marshmallow, PostgreSQL (Docker for local dev)

**Frontend:** Vanilla JavaScript (ES modules), multi-page architecture, no framework — Flask-served static HTML/CSS/JS

**Testing:** pytest, pytest-cov (62 tests, ~85% coverage on core modules)

**Tooling:** Docker Compose (Postgres), Flask CLI (migrations + seed command)

## Architecture

- **Layered backend**: routes → service layer → repository (for aggregate queries) → SQLAlchemy models
- **Role-based access control**: four roles (`reporter`, `support_engineer`, `team_lead`, `admin`), enforced at both the route level (via a `@role_required` decorator) and, where finer-grained ownership/state logic is needed, inside the service layer
- **Enforced status state machine**: incident status transitions are validated against explicit legal-transition and role-permission tables — see [`backend/app/utils/constants.py`](backend/app/utils/constants.py)
- **Append-only audit trail**: every mutating action on an incident (creation, triage, assignment, status change, edits, KB linking) writes a snapshot-based `AuditLog` entry — actor name is snapshotted at write time so history remains accurate even if a user is later renamed or deleted
- **SLA tracking**: response/resolution deadlines computed from priority at triage time, with hold-time bookkeeping that correctly extends deadlines when an incident is placed on hold and resumed

## Project Structure

```
backend/
├── app/
│   ├── models/            # SQLAlchemy models
│   ├── services/           # Business logic, atomic mutations + audit logging
│   ├── repositories/        # Aggregate/complex queries (reporting)
│   ├── routes/               # Flask blueprints
│   ├── schemas/               # Marshmallow request/response schemas
│   └── utils/                  # Constants, SLA calc, decorators, datetime helpers
├── tests/
│   ├── unit/                    # Pure-logic tests (no DB/app context)
│   └── integration/               # Full HTTP request/response tests
├── migrations/                      # Alembic migration history
├── config.py
├── extensions.py
├── seed.py                            # Idempotent demo-data seed command
└── wsgi.py

frontend/
├── *.html                               # Multi-page app: login, dashboard, incident detail, etc.
└── static/
    ├── css/style.css
    └── js/                                 # api.js (shared fetch wrapper), one JS file per page

docker/
└── docker-compose.yml                       # Local Postgres

docs/
└── UAT_PLAN.md                                # Executed user acceptance test walkthrough
```

## Setup

### Prerequisites
- Python 3.9+
- Docker (for local Postgres)

### 1. Clone and set up the virtual environment

```bash
git clone https://github.com/KhalidAlao/Application-Support-and-Incident-Management-Portal.git
cd Application-Support-and-Incident-Management-Portal
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Environment variables

```bash
cp .env.example .env
```

Edit `.env` and set real values for `SECRET_KEY` and `JWT_SECRET_KEY` (generate with `python -c "import secrets; print(secrets.token_hex(32))"`). The default `DATABASE_URL` points to Postgres on port **5433** (as configured in `docker/docker-compose.yml`) to avoid conflicts with a local Postgres installation that may already be using port 5432.

**Note on port 5000**: macOS AirPlay Receiver commonly occupies port 5000. This project defaults `FLASK_RUN_PORT` to `5001` to avoid the conflict.

### 3. Start Postgres

```bash
docker-compose -f docker/docker-compose.yml up -d db
```

### 4. Run migrations

```bash
flask db upgrade
```

### 5. Seed demo data

```bash
flask seed-db
```

This creates four demo users (all password `password`), the four SLA priority tiers, two sample applications, and a handful of sample incidents in varying states.

| Email | Role |
|---|---|
| admin@example.com | admin |
| teamlead@example.com | team_lead |
| engineer@example.com | support_engineer |
| reporter@example.com | reporter |

### 6. Run the app

```bash
flask run
```

Visit `http://localhost:5001/login.html`.

## Running Tests

```bash
python -m pytest backend/tests/ -v
```

With coverage:

```bash
pip install pytest-cov
python -m pytest backend/tests/ --cov=backend/app --cov-report=term-missing
```

Tests run against an isolated in-memory SQLite database per test (see `backend/tests/conftest.py`), separate from the Postgres instance used for local development.

## API Reference

All endpoints except `/api/health` and `/api/auth/login` require a JWT in the `Authorization: Bearer <token>` header. Status transition rules and role permissions are defined in [`backend/app/utils/constants.py`](backend/app/utils/constants.py).

| Method | Endpoint | Description | Permissions / Enforcement |
|---|---|---|---|
| POST | `/api/auth/login` | Login, returns JWT + user info | Public |
| POST | `/api/incidents` | Create a new incident | Any authenticated user — `reporter_id` is taken from JWT |
| GET | `/api/incidents` | List incidents with filtering and pagination | Any authenticated user — reporters see only their own; staff see all |
| GET | `/api/incidents/{id}` | Get incident detail (includes full audit log) | Any authenticated user — reporters only if owner |
| PUT | `/api/incidents/{id}` | Update title/description | Service layer enforces: reporter (own, pre-assignment), assigned `support_engineer`, or `team_lead`/`admin` |
| POST | `/api/incidents/{id}/triage` | Set impact/urgency/priority, compute SLA deadlines | `support_engineer` (if assigned), `team_lead`, `admin` |
| POST | `/api/incidents/{id}/assign` | Assign/reassign incident to a user | `team_lead`, `admin` |
| POST | `/api/incidents/{id}/status` | Change status (state-machine enforced) | Service layer enforces role + transition rules; see `constants.py` |
| GET | `/api/applications` | List active applications | Any authenticated user |
| POST | `/api/applications` | Create a new application | `team_lead`, `admin` |
| GET | `/api/applications/{id}` | Get application by ID | Any authenticated user |
| PUT | `/api/applications/{id}` | Update application fields | `team_lead`, `admin` |
| DELETE | `/api/applications/{id}` | Soft-delete application (sets `is_active=False`) | `team_lead`, `admin` |
| POST | `/api/applications/{id}/reactivate` | Reactivate a soft-deleted application | `team_lead`, `admin` |
| GET | `/api/knowledge` | List all knowledge articles | Any authenticated user |
| POST | `/api/knowledge` | Create a new article | `support_engineer`, `team_lead`, `admin` |
| GET | `/api/knowledge/{id}` | Get a single article | Any authenticated user |
| PUT | `/api/knowledge/{id}` | Update an article | `support_engineer`, `team_lead`, `admin` |
| DELETE | `/api/knowledge/{id}` | Delete an article | `support_engineer`, `team_lead`, `admin` |
| GET | `/api/knowledge/search?q=` | Search articles by title/content/tags (ILIKE) | Any authenticated user |
| POST | `/api/knowledge/{id}/incidents/{incident_id}` | Link an article to an incident | `support_engineer`, `team_lead`, `admin` |
| DELETE | `/api/knowledge/{id}/incidents/{incident_id}` | Unlink an article from an incident | `support_engineer`, `team_lead`, `admin` |
| GET | `/api/reports/summary` | Status counts, total open/closed | `support_engineer`, `team_lead`, `admin` |
| GET | `/api/reports/avg-resolution-time` | Average resolution time (minutes) by priority | `support_engineer`, `team_lead`, `admin` |
| GET | `/api/reports/by-application` | Incident count and avg resolution time per application | `support_engineer`, `team_lead`, `admin` |
| GET | `/api/reports/overdue` | List overdue open incidents (paginated) | `support_engineer`, `team_lead`, `admin` |
| GET | `/api/reports/overdue-count` | Count of overdue open incidents | `support_engineer`, `team_lead`, `admin` |
| GET | `/api/users` | List users (id, name, role) for assignee dropdowns | `support_engineer`, `team_lead`, `admin` (excludes reporters) |
| GET | `/api/health` | Health check | Public |

*(29 endpoints, verified against route decorators in `backend/app/routes/` — see commit history for the verification process.)*

## Known Limitations

This project was built as a structured, phased learning exercise. The following are known, deliberate scope decisions or deferred items rather than oversights:

- **Test coverage**: ~85% on core modules; a small number of repository methods (`get_stats_by_application`, parts of `get_overdue_incidents`) and route error-branches remain untested. Documented as acceptable residual risk rather than chased to 100%.
- **Swagger/OpenAPI**: `flasgger` is installed and wired, but endpoint specs were not written (29 endpoints would require substantial docstring authoring for marginal benefit at this project's scale). A manual API reference table is provided instead.
- **Reporting aggregation**: two report queries (`avg-resolution-time`, `by-application`) compute aggregates in Python rather than via SQL `GROUP BY`/`AVG`, to keep test behavior portable across SQLite (tests) and PostgreSQL (dev/prod). This would not scale well to a very large incidents table; a database-side aggregate rewrite is a documented follow-up.
- **Hold-time/triage interaction**: an incident that accumulates hold time before being triaged will have that hold time recorded, but SLA deadlines computed at triage do not retroactively account for pre-triage hold time. Noted as an edge case, not fixed, given limited real-world likelihood.
- **State machine and priority assignment**: the status state machine does not currently prevent an incident from being placed `on_hold` (or otherwise progressing) without first being triaged; a defensive guard handles this at the service layer instead of preventing it at the transition-table level.
- **Frontend polish**: the UI is functional and covers the full incident lifecycle (create, triage, assign, status transitions, resolution, closure) but CSS styling is utilitarian rather than fully polished.
- **Application audit trail**: `Application` create/update/delete actions are not audit-logged (unlike `Incident` mutations), as a deliberate scope decision — application inventory changes were judged lower-risk than incident-handling accountability.

## Testing Artifacts

- [`docs/UAT_PLAN.md`](docs/UAT_PLAN.md) — a fully executed user acceptance test walkthrough of the complete incident lifecycle (creation → triage → assignment → resolution → closure), including two real gaps found and fixed during execution.