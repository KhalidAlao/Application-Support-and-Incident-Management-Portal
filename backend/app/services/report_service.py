from typing import Dict, List, Any
from backend.app.repositories.incident_repository import IncidentRepository
from backend.app.models import Incident


class ReportService:
    @staticmethod
    def get_summary() -> Dict[str, Any]:
        return IncidentRepository.get_status_summary()

    @staticmethod
    def get_avg_resolution_time() -> List[Dict[str, Any]]:
        return IncidentRepository.get_avg_resolution_time_by_priority()

    @staticmethod
    def get_application_report() -> List[Dict[str, Any]]:
        return IncidentRepository.get_stats_by_application()

    @staticmethod
    def get_overdue_incidents(limit: int = 50) -> List[Dict[str, Any]]:
        incidents = IncidentRepository.get_overdue_incidents(limit)
        return [
            {
                'id': inc.id,
                'title': inc.title,
                'status': inc.status,
                'resolve_due': inc.resolve_due.isoformat() if inc.resolve_due else None,
                'application_id': inc.application_id,
                'assignee_id': inc.assignee_id,
            }
            for inc in incidents
        ]