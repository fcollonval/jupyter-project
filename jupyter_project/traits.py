import abc
import json
import uuid
from pathlib import Path as PyPath
from typing import Any, Dict

import jsonschema
from traitlets import HasTraits, Unicode, TraitError, TraitType, validate
from traitlets.config import Configurable
from traitlets.utils.bunch import Bunch


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

    info_text = "a path string"

    def validate(self, obj, value):
        try:
            return PyPath(value)
        except:
            self.error(obj, value)

class Template(HasTraits):

    destination = Path(default_value=".", help="Relative destination folder", config=True)
    name = Unicode(help="Template name", config=True)
    schema = JSONSchema(help="JSON schema describing the template parameters", config=True)
    template = Unicode(help="Template path", config=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Force checking the default value as they are not valid
        self._valid_name({"value": self.name})
        self._valid_template({"value": self.template})

    def __eq__(self, other: "Template") -> bool:
        for attr in ("destination", "name", "schema", "template"):
            if getattr(self, attr) != getattr(other, attr):
                return False
        return True

    @validate("name")
    def _valid_name(self, proposal: Bunch) -> str:
        if len(proposal["value"]) == 0:
            raise TraitError("'name' cannot be empty.")
        return proposal["value"]

    @validate("template")
    def _valid_template(self, proposal: Bunch) -> str:
        if len(proposal["value"]) == 0:
            raise TraitError("'template' cannot be empty.")
        return proposal["value"]

    @abc.abstractmethod
    def render(self, params: Dict) -> Any:
        """Render the template.
        
        Args:
            params (Dict): Template parameters

        Returns:
            Any : The rendered template.
        """
        raise NotImplementedError()
