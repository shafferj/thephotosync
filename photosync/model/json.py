from __future__ import absolute_import
import json

from sqlalchemy import types


class Json(types.TypeDecorator, types.MutableType):

    impl=types.Text

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        else:
            return json.loads(value)

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        else:
            return json.dumps(value)
