import json
import pathlib
from typing import Any, Dict, NoReturn

import jsonschema
from cookiecutter.main import cookiecutter
from traitlets import HasTraits, TraitError, TraitType, Unicode, validate
from traitlets.utils.bunch import Bunch

from .traits import JSONSchema, Path


class ProjectTemplate(HasTraits):
    """Jinja2 template project class."""

    configuration_filename = Unicode(
        default_value="jupyter-project.json",
        help="Name of the project configuration JSON file [optional]",
        config=True,
    )
    configuration_schema = JSONSchema(
        help="JSON schema describing the project configuration file [optional]", config=True
    )
    default_path = Path(
        help="Default file or folder to open; relative to the project root [optional]", config=True
    )
    # TODO
    module = Unicode(
        help="Python package containing the template [optional]",
        config=True,
    )
    schema = JSONSchema(
        help="JSON schema describing the template parameters [optional]", config=True
    )
    template = Unicode(
        default_value=None,
        allow_none=True,
        help="Cookiecutter template source",
        config=True,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Force checking the default value as they are not valid
        self._valid_template({"value": self.template})

    def __eq__(self, other: "ProjectTemplate") -> bool:
        if self is other:
            return True

        if other is None:  # The first test passes if self == other == None
            return False

        for attr in (
            "configuration_filename",
            "configuration_schema",
            "default_path",
            "schema",
            "template",
        ):
            if getattr(self, attr) != getattr(other, attr):
                return False
        return True

    @validate("template")
    def _valid_template(self, proposal: Bunch) -> str:
        value = proposal["value"]
        if value is not None and len(value) == 0:
            raise TraitError("'template' cannot be empty.")
        return value

    def get_configuration(self, path: pathlib.Path) -> Dict:
        """Get and validate the project configuration in path.
        
        Args:
            path (pathlib.Path): Project folder

        Returns:
            dict: project configuration
        
        Raises:
            ValueError: if the project configuration file does not exists
        """
        if len(self.configuration_filename) == 0 or self.template is None:
            return dict()

        configuration_file = path / self.configuration_filename
        if not configuration_file.exists():
            raise ValueError("Configuration file does not exists.")
        configuration = json.loads(configuration_file.read_text())
        if len(self.configuration_schema) > 0:
            jsonschema.validate(configuration, self.configuration_schema)

        return configuration

    def render(self, params: Dict, path: pathlib.Path) -> Dict:
        """Render the cookiecutter template.
        
        Args:
            params (Dict): Cookiecutter template parameters
            path (pathlib.Path): Path in which the project will be created

        Returns:
            Dict: Project configuration
        """
        if self.template is None:
            return dict()

        cookiecutter(
            self.template, no_input=True, extra_context=params, output_dir=str(path),
        )

        if len(self.configuration_filename) == 0:
            return dict()

        configuration_file = path / self.configuration_filename
        if not configuration_file.exists():
            configuration_file.write_bytes(b"{}")

        return self.get_configuration(path)
