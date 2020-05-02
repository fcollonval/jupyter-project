from ._version import __version__
from .config import JupyterProject
from .handlers import setup_handlers


def _jupyter_server_extension_paths():
    return [{"module": "jupyter_project"}]


def load_jupyter_server_extension(lab_app):
    """Registers the API handler to receive HTTP requests from the frontend extension.

    Parameters
    ----------
    lab_app: jupyterlab.labapp.LabApp
        JupyterLab application instance
    """
    config = JupyterProject(config=lab_app.config)
    setup_handlers(lab_app.web_app, config, lab_app.log)
    lab_app.log.info(
        "Registered jupyter_project extension at URL path /jupyter-project"
    )
