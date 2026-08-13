from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from marshmallow import ValidationError
from backend.app.services.knowledge_service import KnowledgeArticleService
from backend.app.schemas.knowledge import (
    KnowledgeArticleCreateSchema,
    KnowledgeArticleUpdateSchema,
    KnowledgeArticleResponseSchema,
)
from backend.app.models import User
from backend.extensions import db
from backend.app.utils.decorators import role_required
from backend.app.utils.constants import Role

knowledge_bp = Blueprint('knowledge', __name__, url_prefix='/api/knowledge')

create_schema = KnowledgeArticleCreateSchema()
update_schema = KnowledgeArticleUpdateSchema()
response_schema = KnowledgeArticleResponseSchema()


@knowledge_bp.route('', methods=['GET'])
@jwt_required()
def list_articles():
    articles = KnowledgeArticleService.list_articles()
    return jsonify(response_schema.dump(articles, many=True)), 200


@knowledge_bp.route('/search', methods=['GET'])
@jwt_required()
def search_articles():
    q = request.args.get('q', '')
    articles = KnowledgeArticleService.search_articles(q)
    return jsonify(response_schema.dump(articles, many=True)), 200


@knowledge_bp.route('', methods=['POST'])
@jwt_required()
@role_required(Role.SUPPORT_ENGINEER.value, Role.TEAM_LEAD.value, Role.ADMIN.value)
def create_article():
    user_id = int(get_jwt_identity())
    user = db.session.get(User, user_id)
    if not user:
        return jsonify({"error": "User not found"}), 401

    try:
        data = create_schema.load(request.get_json())
    except ValidationError as err:
        return jsonify({"errors": err.messages}), 400

    try:
        article = KnowledgeArticleService.create_article(data, user)
        return jsonify(response_schema.dump(article)), 201
    except PermissionError as e:
        return jsonify({"error": str(e)}), 403


@knowledge_bp.route('/<int:article_id>', methods=['GET'])
@jwt_required()
def get_article(article_id):
    article = KnowledgeArticleService.get_article(article_id)
    if not article:
        return jsonify({"error": "Article not found"}), 404
    return jsonify(response_schema.dump(article)), 200


@knowledge_bp.route('/<int:article_id>', methods=['PUT'])
@jwt_required()
@role_required(Role.SUPPORT_ENGINEER.value, Role.TEAM_LEAD.value, Role.ADMIN.value)
def update_article(article_id):
    user_id = int(get_jwt_identity())
    user = db.session.get(User, user_id)
    if not user:
        return jsonify({"error": "User not found"}), 401

    try:
        data = update_schema.load(request.get_json())
    except ValidationError as err:
        return jsonify({"errors": err.messages}), 400

    try:
        article, msg = KnowledgeArticleService.update_article(article_id, data, user)
        if not article:
            return jsonify({"error": msg}), 404
        return jsonify(response_schema.dump(article)), 200
    except PermissionError as e:
        return jsonify({"error": str(e)}), 403


@knowledge_bp.route('/<int:article_id>', methods=['DELETE'])
@jwt_required()
@role_required(Role.SUPPORT_ENGINEER.value, Role.TEAM_LEAD.value, Role.ADMIN.value)
def delete_article(article_id):
    user_id = int(get_jwt_identity())
    user = db.session.get(User, user_id)
    if not user:
        return jsonify({"error": "User not found"}), 401

    try:
        success, msg = KnowledgeArticleService.delete_article(article_id, user)
        if not success:
            return jsonify({"error": msg}), 404
        return jsonify({"message": msg}), 200
    except PermissionError as e:
        return jsonify({"error": str(e)}), 403


@knowledge_bp.route('/<int:article_id>/incidents/<int:incident_id>', methods=['POST'])
@jwt_required()
@role_required(Role.SUPPORT_ENGINEER.value, Role.TEAM_LEAD.value, Role.ADMIN.value)
def link_article(article_id, incident_id):
    user_id = int(get_jwt_identity())
    user = db.session.get(User, user_id)
    if not user:
        return jsonify({"error": "User not found"}), 401

    success, msg = KnowledgeArticleService.link_to_incident(article_id, incident_id, user)
    if not success:
        return jsonify({"error": msg}), 400
    return jsonify({"message": msg}), 200


@knowledge_bp.route('/<int:article_id>/incidents/<int:incident_id>', methods=['DELETE'])
@jwt_required()
@role_required(Role.SUPPORT_ENGINEER.value, Role.TEAM_LEAD.value, Role.ADMIN.value)
def unlink_article(article_id, incident_id):
    user_id = int(get_jwt_identity())
    user = db.session.get(User, user_id)
    if not user:
        return jsonify({"error": "User not found"}), 401

    success, msg = KnowledgeArticleService.unlink_from_incident(article_id, incident_id, user)
    if not success:
        return jsonify({"error": msg}), 400
    return jsonify({"message": msg}), 200