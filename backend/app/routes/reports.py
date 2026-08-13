from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from backend.app.services.report_service import ReportService
from backend.app.utils.decorators import role_required
from backend.app.utils.constants import Role

reports_bp = Blueprint('reports', __name__, url_prefix='/api/reports')


@reports_bp.route('/summary', methods=['GET'])
@jwt_required()
@role_required(Role.SUPPORT_ENGINEER.value, Role.TEAM_LEAD.value, Role.ADMIN.value)
def summary():
    return jsonify(ReportService.get_summary()), 200


@reports_bp.route('/avg-resolution-time', methods=['GET'])
@jwt_required()
@role_required(Role.SUPPORT_ENGINEER.value, Role.TEAM_LEAD.value, Role.ADMIN.value)
def avg_resolution_time():
    return jsonify(ReportService.get_avg_resolution_time()), 200


@reports_bp.route('/by-application', methods=['GET'])
@jwt_required()
@role_required(Role.SUPPORT_ENGINEER.value, Role.TEAM_LEAD.value, Role.ADMIN.value)
def by_application():
    return jsonify(ReportService.get_application_report()), 200


@reports_bp.route('/overdue', methods=['GET'])
@jwt_required()
@role_required(Role.SUPPORT_ENGINEER.value, Role.TEAM_LEAD.value, Role.ADMIN.value)
def overdue():
    limit = request.args.get('limit', 50, type=int)
    return jsonify(ReportService.get_overdue_incidents(limit)), 200