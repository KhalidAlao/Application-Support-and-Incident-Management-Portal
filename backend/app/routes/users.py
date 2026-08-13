from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required
from backend.app.models import User
from backend.app.utils.decorators import role_required
from backend.app.utils.constants import Role

users_bp = Blueprint('users', __name__, url_prefix='/api/users')

@users_bp.route('', methods=['GET'])
@jwt_required()
@role_required(Role.SUPPORT_ENGINEER.value, Role.TEAM_LEAD.value, Role.ADMIN.value)
def list_users():
    # Only include users eligible to be assignees: exclude reporters
    users = User.query.filter(User.role != Role.REPORTER.value).order_by(User.name).all()
    return jsonify([
        {'id': u.id, 'name': u.name, 'role': u.role}   # email excluded
        for u in users
    ]), 200