"""Schemas of the django-ninja apis"""

from ninja import Schema


class BodyLoginSchema(Schema):
    """Defines schema for the body of a POST /login request."""

    principal: str
    session_password: str
