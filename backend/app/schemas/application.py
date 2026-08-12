from marshmallow import Schema, fields

class ApplicationSchema(Schema):
    id = fields.Int()
    name = fields.Str()
    criticality = fields.Str()
    owner_id = fields.Int(allow_none=True)
    created_at = fields.DateTime()
    updated_at = fields.DateTime()