from typing import Any, Dict

from traitlets import HasTraits, TraitError, TraitType, Unicode, validate
from traitlets.utils.bunch import Bunch

from .traits import JSONSchema, Path


class ProjectTemplate(HasTraits):
    """Jinja2 template project class."""

    schema = JSONSchema(help="JSON schema describing the template parameters", config=True)

    destination = Path(default_value=".", help="Relative destination folder", config=True)
    name = Unicode(help="Template name", config=True)
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

    def render(self, params: Dict) -> Any:
        """Render the template.
        
        Args:
            params (Dict): Template parameters

        Returns:
            Any : The rendered template.
        """
        raise NotImplementedError()
