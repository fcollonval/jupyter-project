import abc
import json
from pathlib import Path as PyPath
from typing import Any, Dict

import jsonschema
from traitlets import HasTraits, Unicode, TraitType
from traitlets.config import Configurable


class Path(TraitType):
    """A path string trait"""
    info_text = 'a path string'

    def validate(self, obj, value):
        try:
            return PyPath(value)
        except:
            self.error(obj, value)


class JSONSchema(TraitType):
    """A JSON schema trait"""
    default_value = dict()
    info_text = 'a JSON schema (defined as string or dictionary)'

    def validate(self, obj, value):
        try:
            if isinstance(value, str):
                value = json.loads(value)

            validator = jsonschema.validators.validator_for(value)
            validator.check_schema(value)
            return value
        except:
            self.error(obj, value)

class Template(HasTraits):

    destination = Path(default_value=".", help="Relative destination folder", config=True)
    name = Unicode(help="Template name", config=True)
    schema = JSONSchema(help="JSON schema describing the template parameters", config=True)
    template = Unicode(help="Template path", config=True)

    def __eq__(self, other: "Template") -> bool:
        for attr in ("destination", "name", "schema", "template"):
            if getattr(self, attr) != getattr(other, attr):
                return False
        return True

    @abc.abstractmethod
    def render(self, params: Dict) -> Any:
        """Render the template.
        
        Args:
            params (Dict): Template parameters

        Returns:
            Any : The rendered template.
        """
        raise NotImplementedError()
