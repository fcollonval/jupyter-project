import pathlib
from typing import Dict

from traitlets import HasTraits, List, TraitError, Unicode, validate
from traitlets.utils.bunch import Bunch

from .autoinstance import AutoInstance
from .traits import JSONSchema, Path


class FileTemplate(HasTraits):
    """Jinja2 file template class."""

    default_name = Unicode(
        default_value="Untitled",
        help="Default file name (without extension; support Jinja2 templating using the schema parameters)",
        config=True,
    )
    destination = Path(help="Relative destination folder [optional]", config=True)
    template_name = Unicode(help="Template name in the UI [optional]", config=True)
    schema = JSONSchema(
        help="JSON schema list describing the templates parameters", config=True
    )
    template = Path(help="Template path", config=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Force checking the default value as they are not valid
        self._valid_template({"value": self.template})

    def __eq__(self, other: "FileTemplate") -> bool:
        if self is other:
            return True

        for attr in ("default_name", "destination", "schema", "template"):
            if getattr(self, attr) != getattr(other, attr):
                return False
        return True

    @validate("default_name")
    def _valid_default_name(self, proposal: Bunch) -> str:
        if len(proposal["value"]) == 0:
            raise TraitError("'default_name' cannot be empty.")
        return proposal["value"]

    @validate("template")
    def _valid_template(self, proposal: Bunch) -> str:
        if proposal["value"] == pathlib.Path(""):
            raise TraitError("'template' cannot be empty.")
        return proposal["value"]


class FileTemplateLoader(HasTraits):
    """Jinja2 template file location class."""

    files = List(
        trait=AutoInstance(FileTemplate),
        minlen=1,
        help="List of template files",
        config=True,
    )
    location = Unicode(help="Templates path", config=True)
    module = Unicode(
        help="Python package containing the templates 'location' [optional]",
        config=True,
    )
    name = Unicode(help="Templates group name", config=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Force checking the default value as they are not valid
        self._valid_name({"value": self.name})
        self._valid_location({"value": self.location})
        if len(self.files) == 0:
            raise TraitError("'files' cannot be empty.")

    def __eq__(self, other: "FileTemplateLoader") -> bool:
        for attr in ("files", "location", "module", "name"):
            if getattr(self, attr) != getattr(other, attr):
                return False
        return True

    @validate("name")
    def _valid_name(self, proposal: Bunch) -> str:
        if len(proposal["value"]) == 0:
            raise TraitError("'name' cannot be empty.")
        return proposal["value"]

    @validate("location")
    def _valid_location(self, proposal: Bunch) -> str:
        if len(proposal["value"]) == 0:
            raise TraitError("'location' cannot be empty.")
        return proposal["value"]
