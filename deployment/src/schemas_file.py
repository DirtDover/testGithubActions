import os
import re

from marshmallow import Schema, ValidationError, fields, validate

LEVEL = ["Easy", "Medium", "Hard"]
KIND = ["path", "track", "course"]
ACCESS = [
    "essentials-full-time",
    "full-stack-full-time",
    "full-stack-part-time",
    "lead-full-time",
    "lead-analysis",
    "analysis-fullstack-full-time",
    "analysis-lead-full-time",
    "cyber-essentials-full-time",
    "cyber-fullstack-full-time",
    "cyber-fullstack-part-time",
    "cyber-lead",
    "courses-free",
    "courses-beginner",
    "courses-intermediate",
    "courses-expert",
    "preview",
    "b2b-saft",
    "teacher-training",
    "jury-training",
    "chatgpt-soge",
]
TYPE = [
    "lecture",
    "exercice",
    "project",
    "code",
    "quiz",
    "video",
    "replay",
    "code-local",
]
TOPIC = [
    "data science and engineering",
    "data analysis",
    "cyber security",
    "cyber security v1",
]
PATH_LEVEL = ["essentials", "fullstack", "lead"]
SCHEDULE = ["full-time", "part-time", "both"]
RESOURCE_TYPE = ["file", "website", "solution"]


def validate_slug(slug: str):
    if not re.match(r"^[a-z0-9]+(?:-[a-z0-9]+)*$", slug):
        raise ValidationError("Slug format is not valid.")


def validate_video_url(url: str):
    if (
        not re.search(r"http[s]{0,1}://www[.]youtube[.]com/watch[?]v=", url)
        and not re.search(r"http[s]{0,1}://youtu[.]be/", url)
        and not re.search(r"http[s]{0,1}://vimeo[.]com/", url)
    ):
        raise ValidationError(
            "Video url format is not valid. It should something like: https://www.youtube.com/watch?v=xxxxxxxxx, https://youtu.be/xxxxxxxxx or https://vimeo.com/xxxxxxxxx."
        )


def validate_teacher_notes(notes: str):
    if not os.path.splitext(notes)[1] in [".md", ".mdx"]:
        raise ValidationError(
            "Teacher notes should be a markdown file with '.md' or '.mdx' extension."
        )
#Planning Keys
#Mandatory
class TimeSlot(Schema):
    start = fields.Str(allow_none=False, required=True)
    end = fields.Str(allow_none=False, required=True)

class ProgramItem(Schema):
    slug = fields.Str(allow_none=False, required=True)
    title = fields.Str(allow_none=False, required=True)
    halfDays = fields.Integer(allow_none=False, required=True)
    rhythm = fields.Str(allow_none=False, required=True)  # "dayFullTime", "evening", etc.
    timeSlots = fields.List(fields.Nested(TimeSlot), allow_none=True, required=True)

class ScheduleType(Schema):
    program = fields.List(fields.Nested(ProgramItem), allow_none=False, required=True)

class Schedule(Schema):
    full_time = fields.Nested(ScheduleType, allow_none=True, required=False)
    part_time = fields.Nested(ScheduleType, allow_none=True, required=False)

class DurationBootcamp(Schema):
    weeks = fields.Integer(allow_none=False, required=True)
    days = fields.Integer(allow_none=False, required=True)
    hours = fields.Float(allow_none=False, required=True)
    
class Planning(Schema):
    bootcampType = fields.Str(allow_none=False, required=True)
    durationBootcamp = fields.Nested(DurationBootcamp, allow_none=False, required=True)
    numberOfModule = fields.Integer(allow_none=False, required=True)
    totalHalfDays = fields.Integer(allow_none=False, required=True)
    totalEvening = fields.Integer(allow_none=False, required=True)
    schedule = fields.Nested(Schedule, allow_none=False, required=True)

class Skill(Schema):
    skill = fields.Str(allow_none=False, required=True)
    ratio = fields.Float(allow_none=True, required=False)


class BaseSchema(Schema):
    # Mandatory
    slug = fields.Str(validate=validate_slug, required=True)
    title = fields.Str(allow_none=False, required=True)
    duration = fields.Str(allow_none=False, required=True)
    kind = fields.Str(validate=validate.OneOf(KIND), required=True)
    # Mandatory in root file
    level = fields.Str(
        validate=validate.OneOf(LEVEL),
        allow_none=False,
        required=False,
    )
    access = fields.Str(
        validate=validate.OneOf(ACCESS),
        allow_none=False,
        required=False,
    )
    topic = fields.Str(
        validate=validate.OneOf(TOPIC),
        allow_none=False,
        required=False,
    )
    pathLevel = fields.Str(
        validate=validate.OneOf(PATH_LEVEL),
        allow_none=False,
        required=False,
    )
    schedule = fields.Str(
        validate=validate.OneOf(SCHEDULE),
        allow_none=False,
        required=False,
    )
    planning = fields.Nested(Planning, allow_none=True, required=False)
    # Optional
    description = fields.Str(allow_none=True, required=False, missing=None)
    goals = fields.List(fields.Str(), allow_none=True, required=False, missing=None)
    tags = fields.List(fields.Str(), allow_none=True, required=False, missing=None)
    prerequisites = fields.List(
        fields.Str(), allow_none=True, required=False, missing=None
    )
    introductionVideoId = fields.Str(allow_none=True, required=False, missing=None)
    points = fields.Number(allow_none=True, required=False)
    skills = fields.List(fields.Nested(Skill), allow_none=True, required=False)
    halfDays = fields.Integer(allow_none=True, required=False)
    isWorkingDay = fields.Boolean(allow_none=True, required=False)
    createdDate = fields.Str(allow_none=True, required=False)
    difficulty = fields.Number(allow_none=True, required=False)


class ResourceSchema(Schema):
    title = fields.Str(allow_none=False, required=True)
    target = fields.Str(allow_none=False, required=True)
    type = fields.Str(
        validate=validate.OneOf(RESOURCE_TYPE), allow_none=True, required=False
    )


class ContentSchema(Schema):
    content = fields.Str(allow_none=False, required=True)
    slug = fields.Str(validate=validate_slug, allow_none=False, required=True)
    title = fields.Str(allow_none=False, required=True)
    type = fields.Str(
        validate=validate.OneOf(TYPE),
        allow_none=False,
        required=True,
    )
    duration = fields.Integer(allow_none=False, required=True)
    resources = fields.List(
        fields.Nested(ResourceSchema), allow_none=True, required=True
    )
    points = fields.Number(allow_none=True, required=False)
    skills = fields.Dict(allow_none=True, required=False)
    multiplier = fields.Number(allow_none=True, required=False)
    solution = fields.Str(allow_none=False, required=False)


class FileBaseSchema(BaseSchema):
    children = fields.List(fields.Str(), allow_none=False, required=True)


class TeacherNotesSchema(Schema):
    content = fields.Str(
        validate=validate_teacher_notes, required=True, allow_none=False
    )
    resources = fields.List(
        fields.Nested(ResourceSchema), allow_none=True, required=True
    )


class FileCourseBaseSchema(BaseSchema):
    children = fields.List(
        fields.Nested(ContentSchema), allow_none=False, required=True
    )
    replay = fields.Str(validate=validate_video_url, allow_none=False, required=False)
    replay_fr = fields.Str(
        validate=validate_video_url, allow_none=False, required=False
    )
    replay_en = fields.Str(
        validate=validate_video_url, allow_none=False, required=False
    )
    notes = fields.Nested(TeacherNotesSchema, required=False, allow_none=False)


class AnswerQuizSchema(Schema):
    label = fields.Raw(allow_none=False, required=True)
    correct = fields.Bool(allow_none=False, required=False)


class QuestionQuizSchema(Schema):
    title = fields.Str(allow_none=False, required=True)
    statement = fields.Str(allow_none=True, required=False)
    explanation = fields.Str(allow_none=True, required=False)
    bonus = fields.Bool(allow_none=False, required=False)
    answers = fields.List(
        fields.Nested(AnswerQuizSchema), allow_none=False, required=True
    )


class QuizSchema(Schema):
    questions = fields.List(
        fields.Nested(QuestionQuizSchema), allow_none=False, required=True
    )


class QuizCodeSchema(Schema):
    instruction = fields.Str(allow_none=False, required=True)
    default = fields.Str(allow_none=True, required=False)
    assessment = fields.Str(allow_none=False, required=True)
    packages = fields.List(fields.Str(), allow_none=True, required=False)
    packagesExternal = fields.List(fields.Str(), allow_none=True, required=False)

