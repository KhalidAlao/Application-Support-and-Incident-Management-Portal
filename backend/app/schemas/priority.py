from marshmallow import Schema, fields

class PrioritySchema(Schema):
    id = fields.Int()
    code = fields.Str()
    label = fields.Str()
    impact_level = fields.Str()
    urgency_level = fields.Str()
    response_minutes = fields.Int()
    resolution_minutes = fields.Int()