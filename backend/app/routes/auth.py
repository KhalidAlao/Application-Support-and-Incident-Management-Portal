from flask import Blueprint, request, jsonify
from marshmallow import Schema, fields, ValidationError
from backend.app.services.auth_service import AuthService

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')

class LoginSchema(Schema):
    email = fields.Email(required=True, error_messages={"required": "Email is required"})
    password = fields.Str(required=True, error_messages={"required": "Password is required"})

login_schema = LoginSchema()

@auth_bp.route('/login', methods=['POST'])
def login():
    """Authenticate user and return JWT access token."""
    try:
        data = login_schema.load(request.get_json())
    except ValidationError as err:
        return jsonify({"errors": err.messages}), 400

    user, error = AuthService.authenticate_user(data['email'], data['password'])
    if error:
        return jsonify({"error": error}), 401

    access_token = AuthService.create_token(user)

    return jsonify({
        "access_token": access_token,
        "user": {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "role": user.role
        },
        "expires_in": 3600
    }), 200