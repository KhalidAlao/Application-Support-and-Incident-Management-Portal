from marshmallow import Schema, fields, validate
from backend.app.utils.constants import CriticalityLevel

# Simple schema for nested incident responses (minimal fields)
class ApplicationSchema(Schema):
    id = fields.Int()
    name = fields.Str()
    criticality = fields.Str()

# Detailed schemas for CRUD

class ApplicationCreateSchema(Schema):
    name = fields.Str(required=True, validate=validate.Length(min=1, max=100))
    description = fields.Str(allow_none=True)
    criticality = fields.Str(
        required=True,
        validate=validate.OneOf([v.value for v in CriticalityLevel])
    )
    owner_id = fields.Int(required=True, validate=validate.Range(min=1))

class ApplicationUpdateSchema(Schema):
    name = fields.Str(validate=validate.Length(min=1, max=100))
    description = fields.Str(allow_none=True)
    criticality = fields.Str(
        validate=validate.OneOf([v.value for v in CriticalityLevel])
    )
    owner_id = fields.Int(validate=validate.Range(min=1))

class ApplicationResponseSchema(Schema):
    id = fields.Int()
    name = fields.Str()
    description = fields.Str(allow_none=True)
    criticality = fields.Str()
    owner_id = fields.Int()
    is_active = fields.Bool()
    created_at = fields.DateTime()
    updated_at = fields.DateTime()