from marshmallow import Schema, fields

class AuditLogSchema(Schema):
    id = fields.Int()
    field_changed = fields.Str()
    old_value = fields.Str(allow_none=True)
    new_value = fields.Str(allow_none=True)
    actor_name = fields.Str()
    reason = fields.Str(allow_none=True)
    timestamp = fields.DateTime()