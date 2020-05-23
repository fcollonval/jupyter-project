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
        help="List of file template loaders",
        config=True,
    )

    project_template = AutoInstance(
        ProjectTemplate,
        allow_none=True,
        help="The project template options",
        config=True,
    )
