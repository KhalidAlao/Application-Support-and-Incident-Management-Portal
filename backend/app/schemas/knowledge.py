from marshmallow import Schema, fields, validate

class KnowledgeArticleCreateSchema(Schema):
    title = fields.Str(required=True, validate=validate.Length(min=1, max=200))
    content = fields.Str(required=True, validate=validate.Length(min=1))
    tags = fields.Str(allow_none=True, validate=validate.Length(max=500))

class KnowledgeArticleUpdateSchema(Schema):
    title = fields.Str(validate=validate.Length(min=1, max=200))
    content = fields.Str(validate=validate.Length(min=1))
    tags = fields.Str(allow_none=True, validate=validate.Length(max=500))

class KnowledgeArticleResponseSchema(Schema):
    id = fields.Int()
    title = fields.Str()
    content = fields.Str()
    tags = fields.Str(allow_none=True)
    author_id = fields.Int()
    created_at = fields.DateTime()
    updated_at = fields.DateTime()

class KnowledgeArticleSummarySchema(Schema):
    id = fields.Int()
    title = fields.Str()