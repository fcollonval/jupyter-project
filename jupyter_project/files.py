from pathlib import Path
from typing import Dict

from .traits import Template


class FileTemplate(Template):
    """Jinja2 template file class."""

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
