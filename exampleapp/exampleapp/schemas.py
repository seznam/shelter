"""Schemas module"""
from marshmallow import Schema, fields


class BaseSchema(Schema):
    class Meta:
        ordered = True
