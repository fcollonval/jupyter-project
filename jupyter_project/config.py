from traitlets import List, Unicode
from traitlets.config import Configurable

from .autoinstance import AutoInstance
from .files import FileTemplateLoader
from .project import ProjectTemplate


class JupyterProject(Configurable):
    """Configuration for jupyter-project server extension."""

    file_templates = List(
        default_value=list(),
        trait=AutoInstance(FileTemplateLoader),
        help="List of file templates",
        config=True,
    )

    project_file = Unicode(
        default_value="jupyter-project.json",
        help="Name of the project configuration file",
        config=True,
    )

    project_template = AutoInstance(
        ProjectTemplate,
        kw=dict(
            name="drivendata",
            template="https://github.com/drivendata/cookiecutter-data-science",
        ),
        help="The project cookiecutter template (can be local path or URL).",
        config=True,
    )
