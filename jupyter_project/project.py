import importlib
import json
import logging
import pathlib
from typing import Any, Dict, NoReturn, Tuple

from jinja2 import (
    Template,
    TemplateError,
)
import jsonschema
from cookiecutter.main import cookiecutter
from traitlets import Bool, HasTraits, TraitError, TraitType, Unicode, validate
from traitlets.utils.bunch import Bunch

from .jinja2 import jinja2_extensions
from .traits import JSONSchema, Path

logger = logging.getLogger(__name__)


class ProjectTemplate(HasTraits):
    """Jinja2 template project class."""

    configuration_filename = Unicode(
        default_value="jupyter-project.json",
        help="Name of the project configuration JSON file [optional]",
        config=True,
    )
    configuration_schema = JSONSchema(
        default_value={
            "type": "object",
            "properties": {"name": {"type": "string"}},
            "required": ["name"],
        },
        help="JSON schema describing the project configuration file [optional]",
        config=True,
    )
    conda_pkgs = Unicode(
        default_value=None,
        allow_none=True,
        help="Type of conda environment or space separated list of conda packages (requires `jupyter_conda`) [optional]",
        config=True
    )
    default_path = Path(
        help="Default file or folder to open; relative to the project root [optional]",
        config=True,
    )
    editable_install = Bool(
        default_value=True,
        help="Should the project be installed in pip editable mode in the conda environment?",
        config=True,
    )
    filter_kernel = Bool(
        default_value=True,
        help="Should the kernel be filtered to match only the conda environment?",
        config=True,
    )
    folder_name = Unicode(
        default_value="{{ name|lower|replace(' ', '_') }}",
        help="Project name (support Jinja2 templating using the schema parameters) [optional]",
        config=True,
    )
    module = Unicode(
        help="Python package containing the template [optional]", config=True,
    )
    schema = JSONSchema(
        default_value={
            "type": "object",
            "properties": {"name": {"type": "string", "pattern": "^[a-zA-Z_]\\w*$"}},
            "required": ["name"],
        },
        help="JSON schema describing the template parameters [optional]",
        config=True,
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
        self._folder_name = Template(self.folder_name, extensions=jinja2_extensions)

    def __eq__(self, other: "ProjectTemplate") -> bool:
        if self is other:
            return True

        if other is None:  # The first test passes if self == other == None
            return False

        for attr in (
            "configuration_filename",
            "configuration_schema",
            "default_path",
            "editable_install",
            "filter_kernel",
            "folder_name",
            "module",
            "schema",
            "template",
        ):
            if getattr(self, attr) != getattr(other, attr):
                return False
        return True

    @validate("folder_name")
    def _valid_folder_name(self, proposal: Bunch) -> str:
        if len(proposal["value"]) == 0:
            raise TraitError("'folder_name' cannot be empty.")
        self._folder_name = Template(proposal["value"], extensions=jinja2_extensions)
        return proposal["value"]

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

    def render(self, params: Dict, path: pathlib.Path) -> Tuple[str, Dict]:
        """Render the cookiecutter template.
        
        Args:
            params (Dict): Cookiecutter template parameters
            path (pathlib.Path): Path in which the project will be created

        Returns:
            Tuple[str, Dict]: (Project folder name, Project configuration)
        """
        if self.template is None:
            return None, dict()

        try:
            folder_name = self._folder_name.render(**params)
        except TemplateError as error:
            raise ValueError("Project 'folder_name' cannot be rendered.")

        project_name = folder_name.replace("_", " ").capitalize()

        if len(self.module):
            module = importlib.import_module(self.module)
            template = str(pathlib.Path(module.__path__[0]) / self.template)
        else:
            template = self.template

        cookiecutter(
            template, no_input=True, extra_context=params, output_dir=str(path),
        )

        content = {"name": project_name}
        if len(self.configuration_filename) > 0:
            configuration_file = path / folder_name / self.configuration_filename
            if configuration_file.exists():
                try:
                    content = json.loads(configuration_file.read_text())
                except json.JSONDecodeError as error:
                    logger.debug(
                        f"Unable to load configuration file {configuration_file!s}:\n{error!s}"
                    )
                else:
                    content["name"] = project_name
            configuration_file.parent.mkdir(parents=True, exist_ok=True)
            configuration_file.write_text(json.dumps(content))

            content = self.get_configuration(configuration_file.parent)

        return folder_name, content
