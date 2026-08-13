from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from marshmallow import ValidationError
from backend.app.services.application_service import ApplicationService
from backend.app.schemas.application import (
    ApplicationCreateSchema,
    ApplicationUpdateSchema,
    ApplicationResponseSchema,
)
from backend.app.models import User
from backend.extensions import db
from backend.app.utils.decorators import role_required
from backend.app.utils.constants import Role

applications_bp = Blueprint('applications', __name__, url_prefix='/api/applications')

create_schema = ApplicationCreateSchema()
update_schema = ApplicationUpdateSchema()
response_schema = ApplicationResponseSchema()


@applications_bp.route('', methods=['GET'])
@jwt_required()
def list_applications():
    """List applications, optionally including inactive."""
    include_inactive = request.args.get('include_inactive', 'false').lower() == 'true'
    apps = ApplicationService.get_applications(include_inactive=include_inactive)
    return jsonify(response_schema.dump(apps, many=True)), 200


@applications_bp.route('', methods=['POST'])
@jwt_required()
@role_required(Role.TEAM_LEAD.value, Role.ADMIN.value)
def create_application():
    user_id = int(get_jwt_identity())
    user = db.session.get(User, user_id)
    if not user:
        return jsonify({"error": "User not found"}), 401

    try:
        data = create_schema.load(request.get_json())
    except ValidationError as err:
        return jsonify({"errors": err.messages}), 400

    try:
        app = ApplicationService.create_application(data, user)
        return jsonify(response_schema.dump(app)), 201
    except PermissionError as e:
        return jsonify({"error": str(e)}), 403
    except ValueError as e:
        return jsonify({"error": str(e)}), 404


@applications_bp.route('/<int:app_id>', methods=['GET'])
@jwt_required()
def get_application(app_id):
    app = ApplicationService.get_application(app_id)
    if not app:
        return jsonify({"error": "Application not found"}), 404
    return jsonify(response_schema.dump(app)), 200


@applications_bp.route('/<int:app_id>', methods=['PUT'])
@jwt_required()
@role_required(Role.TEAM_LEAD.value, Role.ADMIN.value)
def update_application(app_id):
    user_id = int(get_jwt_identity())
    user = db.session.get(User, user_id)
    if not user:
        return jsonify({"error": "User not found"}), 401

    try:
        data = update_schema.load(request.get_json())
    except ValidationError as err:
        return jsonify({"errors": err.messages}), 400

    try:
        app, msg = ApplicationService.update_application(app_id, data, user)
        if not app:
            return jsonify({"error": msg}), 404
        return jsonify(response_schema.dump(app)), 200
    except PermissionError as e:
        return jsonify({"error": str(e)}), 403
    except ValueError as e:
        return jsonify({"error": str(e)}), 404


@applications_bp.route('/<int:app_id>', methods=['DELETE'])
@jwt_required()
@role_required(Role.TEAM_LEAD.value, Role.ADMIN.value)
def deactivate_application(app_id):
    """Soft-delete an application by setting is_active=False."""
    user_id = int(get_jwt_identity())
    user = db.session.get(User, user_id)
    if not user:
        return jsonify({"error": "User not found"}), 401

    try:
        success, msg = ApplicationService.deactivate_application(app_id, user)
        if not success:
            return jsonify({"error": msg}), 404
        return jsonify({"message": msg}), 200
    except PermissionError as e:
        return jsonify({"error": str(e)}), 403


@applications_bp.route('/<int:app_id>/reactivate', methods=['POST'])
@jwt_required()
@role_required(Role.TEAM_LEAD.value, Role.ADMIN.value)
def reactivate_application(app_id):
    """Reactivate a soft-deleted application."""
    user_id = int(get_jwt_identity())
    user = db.session.get(User, user_id)
    if not user:
        return jsonify({"error": "User not found"}), 401

    try:
        success, msg = ApplicationService.reactivate_application(app_id, user)
        if not success:
            return jsonify({"error": msg}), 404
        return jsonify({"message": msg}), 200
    except PermissionError as e:
        return jsonify({"error": str(e)}), 403