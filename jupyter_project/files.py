from pathlib import Path
from typing import Dict

from traitlets import List, Unicode

from .traits import JSONSchema, Path, Template


class FileTemplate(Template):
    """Jinja2 template file class."""

    files = List(trait=Path(), minlen=1, help="List of template files", config=True)
    module = Unicode(help="Python package containing the template [optional]", config=True)
    schemas = List(trait=JSONSchema(), help="JSON schema list describing the templates parameters", config=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def render(self, params: Dict) -> str:
        """Render the Jinja2 template.
        
        Args:
            params (Dict): Template parameters

        Returns:
            str : The rendered template.
        """
        raise NotImplementedError()
