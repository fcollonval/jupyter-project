from typing import Any, Dict

from .traits import Template


class ProjectTemplate(Template):
    def render(self, params: Dict) -> Any:
        """Render the template.
        
        Args:
            params (Dict): Template parameters

        Returns:
            Any : The rendered template.
        """
        raise NotImplementedError()
