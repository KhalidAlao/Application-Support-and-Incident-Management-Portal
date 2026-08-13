from marshmallow import Schema, fields, validate, ValidationError
from datetime import datetime
from backend.app.utils.constants import IncidentStatus, ImpactLevel, UrgencyLevel, ResolutionCode
from .knowledge import KnowledgeArticleSummarySchema

class IncidentCreateSchema(Schema):
    """Schema for creating a new incident (POST /api/incidents)."""
    title = fields.Str(required=True, validate=validate.Length(min=1, max=200))
    description = fields.Str(required=True, validate=validate.Length(min=1))
    reported_priority_text = fields.Str(allow_none=True, validate=validate.Length(max=255))
    application_id = fields.Int(required=True, validate=validate.Range(min=1))


class IncidentUpdateSchema(Schema):
    """Schema for updating an incident (PUT /api/incidents/:id)."""
    title = fields.Str(validate=validate.Length(min=1, max=200))
    description = fields.Str(validate=validate.Length(min=1))


class IncidentTriageSchema(Schema):
    """Schema for triaging an incident (POST /api/incidents/:id/triage)."""
    impact = fields.Str(required=True, validate=validate.OneOf([v.value for v in ImpactLevel]))
    urgency = fields.Str(required=True, validate=validate.OneOf([v.value for v in UrgencyLevel]))
    priority_code = fields.Str(required=True, validate=validate.OneOf(['P1', 'P2', 'P3', 'P4']))


class IncidentStatusUpdateSchema(Schema):
    """Schema for updating incident status (POST /api/incidents/:id/status)."""
    status = fields.Str(required=True, validate=validate.OneOf([v.value for v in IncidentStatus]))
    reason = fields.Str(allow_none=True, validate=validate.Length(max=500))  # FIXED: use validate.Length


class IncidentResponseSchema(Schema):
    """Schema for incident response (GET /api/incidents)."""
    id = fields.Int()
    title = fields.Str()
    description = fields.Str()
    reported_priority_text = fields.Str(allow_none=True)
    impact = fields.Str(allow_none=True)
    urgency = fields.Str(allow_none=True)
    status = fields.Str()
    response_due = fields.DateTime(allow_none=True)
    resolve_due = fields.DateTime(allow_none=True)
    total_hold_minutes = fields.Int()
    hold_started_at = fields.DateTime(allow_none=True)
    resolution_code = fields.Str(allow_none=True)
    created_at = fields.DateTime()
    updated_at = fields.DateTime()
    reporter_id = fields.Int()
    assignee_id = fields.Int(allow_none=True)
    application_id = fields.Int()
    assigned_priority_id = fields.Int(allow_none=True)
    resolved_at = fields.DateTime(allow_none=True)

    # Nested objects for convenience
    reporter = fields.Nested('UserSchema', only=('id', 'name', 'email'), allow_none=True)
    assignee = fields.Nested('UserSchema', only=('id', 'name', 'email'), allow_none=True)
    application = fields.Nested('ApplicationSchema', only=('id', 'name'), allow_none=True)
    priority = fields.Nested('PrioritySchema', only=('id', 'code', 'label'), allow_none=True)
    knowledge_articles = fields.List(fields.Nested(KnowledgeArticleSummarySchema))


class IncidentListResponseSchema(Schema):
    """Schema for list response (GET /api/incidents)."""
    items = fields.List(fields.Nested(IncidentResponseSchema))
    total = fields.Int()
    page = fields.Int()
    per_page = fields.Int()
    pages = fields.Int()
    
class IncidentStatusUpdateSchema(Schema):
    status = fields.Str(required=True, validate=validate.OneOf([v.value for v in IncidentStatus]))
    reason = fields.Str(allow_none=True, validate=validate.Length(max=500))
    resolution_code = fields.Str(allow_none=True, validate=validate.OneOf([v.value for v in ResolutionCode]))