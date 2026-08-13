from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from marshmallow import ValidationError
from backend.app.services.incident_service import IncidentService
from backend.app.schemas import (
    IncidentCreateSchema,
    IncidentUpdateSchema,
    IncidentTriageSchema,
    IncidentStatusUpdateSchema,
    IncidentResponseSchema,
    IncidentListResponseSchema,
    UserSchema,
    ApplicationSchema,
    PrioritySchema,
)
from backend.app.models import User, Application, Priority
from backend.app.utils.decorators import role_required
from backend.app.utils.constants import Role

from backend.extensions import db

incidents_bp = Blueprint('incidents', __name__, url_prefix='/api/incidents')

# Schemas
create_schema = IncidentCreateSchema()
update_schema = IncidentUpdateSchema()
triage_schema = IncidentTriageSchema()
response_schema = IncidentResponseSchema()
list_schema = IncidentListResponseSchema()
user_schema = UserSchema()
app_schema = ApplicationSchema()
priority_schema = PrioritySchema()


@incidents_bp.route('', methods=['POST'])
@jwt_required()
def create_incident():
    """Create a new incident."""
    current_user_id = int(get_jwt_identity())
    user = db.session.get(User, current_user_id)
    if not user:
        return jsonify({"error": "User not found"}), 401

    try:
        data = create_schema.load(request.get_json())
    except ValidationError as err:
        return jsonify({"errors": err.messages}), 400

    incident = IncidentService.create_incident(data, user)
    return jsonify(response_schema.dump(incident)), 201


@incidents_bp.route('', methods=['GET'])
@jwt_required()
def list_incidents():
    """List incidents with role-aware filtering and pagination."""
    current_user_id = int(get_jwt_identity())
    user = db.session.get(User, current_user_id)
    if not user:
        return jsonify({"error": "User not found"}), 401

    # Parse query parameters
    status = request.args.get('status')
    application_id = request.args.get('application_id', type=int)
    assignee_id = request.args.get('assignee_id', type=int)
    created_after = request.args.get('created_after')
    created_before = request.args.get('created_before')
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)

    # Date parsing (simplified – can be extended)
    created_after_dt = None
    created_before_dt = None
    if created_after:
        try:
            from datetime import datetime
            created_after_dt = datetime.fromisoformat(created_after.replace('Z', '+00:00'))
        except ValueError:
            return jsonify({"error": "Invalid created_after format (use ISO 8601)"}), 400
    if created_before:
        try:
            from datetime import datetime
            created_before_dt = datetime.fromisoformat(created_before.replace('Z', '+00:00'))
        except ValueError:
            return jsonify({"error": "Invalid created_before format (use ISO 8601)"}), 400

    items, total, page, pages = IncidentService.get_incidents(
        current_user=user,
        status=status,
        application_id=application_id,
        assignee_id=assignee_id,
        created_after=created_after_dt,
        created_before=created_before_dt,
        page=page,
        per_page=per_page
    )

    # Serialize with nested objects
    result = {
        'items': response_schema.dump(items, many=True),
        'total': total,
        'page': page,
        'per_page': per_page,
        'pages': pages,
    }
    return jsonify(result), 200


@incidents_bp.route('/<int:incident_id>', methods=['GET'])
@jwt_required()
def get_incident(incident_id):
    """Get a single incident by ID."""
    current_user_id = int(get_jwt_identity())
    user = db.session.get(User, current_user_id)
    if not user:
        return jsonify({"error": "User not found"}), 401

    incident = IncidentService.get_incident(incident_id, user)
    if not incident:
        return jsonify({"error": "Incident not found"}), 404

    return jsonify(response_schema.dump(incident)), 200


@incidents_bp.route('/<int:incident_id>', methods=['PUT'])
@jwt_required()
def update_incident(incident_id):
    """Update an incident (title/description)."""
    current_user_id = int(get_jwt_identity())
    user = db.session.get(User, current_user_id)
    if not user:
        return jsonify({"error": "User not found"}), 401

    try:
        data = update_schema.load(request.get_json())
    except ValidationError as err:
        return jsonify({"errors": err.messages}), 400

    incident, status_code, message = IncidentService.update_incident(incident_id, data, user)
    if not incident and status_code == 404:
        return jsonify({"error": message}), 404
    if not incident and status_code == 403:
        return jsonify({"error": message}), 403

    return jsonify(response_schema.dump(incident)), status_code


@incidents_bp.route('/<int:incident_id>/triage', methods=['POST'])
@jwt_required()
@role_required(Role.SUPPORT_ENGINEER.value, Role.TEAM_LEAD.value, Role.ADMIN.value)
def triage_incident(incident_id):
    """Triage an incident: set impact, urgency, priority, SLA deadlines."""
    current_user_id = int(get_jwt_identity())
    user = db.session.get(User, current_user_id)
    if not user:
        return jsonify({"error": "User not found"}), 401

    try:
        data = triage_schema.load(request.get_json())
    except ValidationError as err:
        return jsonify({"errors": err.messages}), 400

    incident, status_code, message = IncidentService.triage_incident(
        incident_id,
        data['impact'],
        data['urgency'],
        data['priority_code'],
        user
    )
    if not incident:
        return jsonify({"error": message}), status_code

    return jsonify(response_schema.dump(incident)), 200

@incidents_bp.route('/<int:incident_id>/assign', methods=['POST'])
@jwt_required()
@role_required(Role.TEAM_LEAD.value, Role.ADMIN.value)
def assign_incident(incident_id):
    current_user_id = int(get_jwt_identity())
    user = db.session.get(User, current_user_id)
    if not user:
        return jsonify({"error": "User not found"}), 401

    data = request.get_json()
    if not data or 'assignee_id' not in data:
        return jsonify({"error": "assignee_id is required"}), 400

    incident, status_code, message = IncidentService.assign_incident(
        incident_id, data['assignee_id'], user
    )
    if not incident:
        return jsonify({"error": message}), status_code
    return jsonify(response_schema.dump(incident)), 200


@incidents_bp.route('/<int:incident_id>/status', methods=['POST'])
@jwt_required()
def update_status(incident_id):
    current_user_id = int(get_jwt_identity())
    user = db.session.get(User, current_user_id)
    if not user:
        return jsonify({"error": "User not found"}), 401

    try:
        data = IncidentStatusUpdateSchema().load(request.get_json())
    except ValidationError as err:
        return jsonify({"errors": err.messages}), 400

    incident, status_code, message = IncidentService.update_status(
        incident_id,
        data['status'],
        user,
        data.get('reason'),
        data.get('resolution_code')
    )
    if not incident:
        return jsonify({"error": message}), status_code
    return jsonify(response_schema.dump(incident)), 200