import json
from pathlib import Path as PyPath

import jsonschema
from traitlets import TraitType, validate


class JSONSchema(TraitType):
    """A JSON schema trait"""

    default_value = dict()
    info_text = "a JSON schema (defined as string or dictionary)"

    def validate(self, obj, value):
        try:
            if isinstance(value, str):
                value = json.loads(value)

            validator = jsonschema.validators.validator_for(value)
            validator.check_schema(value)
            return value
        except:
            self.error(obj, value)


class Path(TraitType):
    """A path string trait"""

    default_value = "."
    info_text = "a path string"

    def validate(self, obj, value):
        try:
            return PyPath(value)
        except:
            self.error(obj, value)
