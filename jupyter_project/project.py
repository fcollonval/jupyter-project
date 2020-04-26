from typing import Any, Dict

from .traits import JSONSchema, Template


class ProjectTemplate(Template):
    """Jinja2 template project class."""

    schema = JSONSchema(help="JSON schema describing the template parameters", config=True)

    def render(self, params: Dict) -> Any:
        """Render the template.
        
        Args:
            params (Dict): Template parameters

        Returns:
            Any : The rendered template.
        """
        raise NotImplementedError()
