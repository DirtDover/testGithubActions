from marshmallow import Schema, fields, validate
from src.schemas_file import (
    KIND,
    LEVEL,
    RESOURCE_TYPE,
    TYPE,
    TOPIC,
    PATH_LEVEL,
    SCHEDULE,
    validate_slug,
)

CATEGORIES = ["online", "degree"]


class ParentSchema(Schema):
    slug = fields.Str(allow_none=False, required=True)
    kind = fields.Str(validate=validate.OneOf(KIND), allow_none=False, required=True)


class Skill(Schema):
    skill = fields.Str(allow_none=False, required=True)
    ratio = fields.Float(allow_none=True, required=False)


class BaseSchema(Schema):
    slug = fields.Str(validate=validate_slug, required=True)
    title = fields.Str(required=True)
    level = fields.Str(validate=validate.OneOf(LEVEL), required=True)
    link = fields.Str(required=True)
    duration = fields.Str(required=True)
    minutes = fields.Integer(required=True)
    modules = fields.Integer(required=True)
    illustration = fields.Str(required=True)
    gradient = fields.Str(required=True)
    type = fields.Str(required=True)
    introductionVideoId = fields.Str(allow_none=True, required=True)
    description = fields.Str(allow_none=True, required=True)
    goals = fields.List(fields.Str(), allow_none=True, required=True)
    prerequisites = fields.List(fields.Str(), allow_none=True, required=True)
    tags = fields.List(fields.Str(), allow_none=True, required=True)
    access = fields.Str(allow_none=False, required=True)
    parents = fields.List(fields.Nested(ParentSchema), allow_none=True, required=True)
    children = fields.List(fields.Str(), allow_none=True, required=False)
    category = fields.Str(
        validate=validate.OneOf(CATEGORIES), allow_none=False, required=True
    )
    points = fields.Number(allow_none=True, required=False)
    skills = fields.List(fields.Nested(Skill), allow_none=True, required=False)
    topic = fields.Str(validate=validate.OneOf(TOPIC), allow_none=True, required=False)
    pathLevel = fields.Str(
        validate=validate.OneOf(PATH_LEVEL), allow_none=True, required=False
    )
    schedule = fields.Str(
        validate=validate.OneOf(SCHEDULE), allow_none=True, required=False
    )
    halfDays = fields.Integer(allow_none=True, required=False)


class ResourceSchema(Schema):
    name = fields.Str(required=True)
    link = fields.Str(required=True)
    type = fields.Str(
        validate=validate.OneOf(RESOURCE_TYPE), allow_none=True, required=False
    )


class ContentSchema(Schema):
    slug = fields.Str(required=True)
    title = fields.Str(required=True)
    type = fields.Str(
        validate=validate.OneOf(TYPE),
        required=True,
    )
    duration = fields.Integer(required=True)
    content = fields.Str(required=True)
    link = fields.Str(required=True)
    prevLink = fields.Str(required=True)
    nextLink = fields.Str(required=True)
    resources = fields.List(
        fields.Nested(ResourceSchema), allow_none=True, required=True
    )
    points = fields.Number(allow_none=True, required=False)
    skills = fields.List(fields.Nested(Skill), allow_none=True, required=False)
    multiplier = fields.Number(allow_none=True, required=False)
    source = fields.Str(allow_none=True, required=False)
    solution = fields.Str(allow_none=False, required=False)


class CourseSchema(BaseSchema):
    children = fields.List(fields.Nested(ContentSchema), allow_none=True, required=True)
    notes = fields.Bool(allow_none=False, required=False)
    isWorkingDay = fields.Boolean(allow_none=True, required=False)


class ContentsInDatabaseSchema(Schema):
    """This schema describe documents in `contents` collection.

    It is used for teacher notes and exercices solutions so as to lean pages in
    JULIE.
    """

    slug = fields.Str(validate=validate_slug, allow_none=False, required=True)
    content = fields.Str(allow_none=False, required=True)
    resources = fields.List(
        fields.Nested(ResourceSchema), allow_none=True, required=True
    )
