import functools
import json
import logging
from pathlib import Path
from shutil import rmtree
from typing import Any, Dict
from urllib.parse import quote

from cookiecutter.exceptions import CookiecutterException
from jinja2 import (
    Environment,
    FileSystemLoader,
    PackageLoader,
    PrefixLoader,
    Template,
    TemplateError,
)
from jsonschema.exceptions import ValidationError
from jupyter_client.jsonutil import date_default
from notebook.base.handlers import APIHandler, path_regex
from notebook.utils import url_path_join, url2path
import tornado

from .config import JupyterProject, ProjectTemplate
from .jinja2 import jinja2_extensions

NAMESPACE = "jupyter-project"


class FileTemplatesHandler(APIHandler):
    """Handler for generating file from templates."""

    def initialize(self, default_name: str = None, template: Template = None):
        """Initialize request handler

        Args:
            default_name (str): File default name - will be rendered with same parameters than template
            template (jinja2.Template): Jinja2 template to use for component generation.
        """
        self.default_name = Template(
            default_name or "Untitled", extensions=jinja2_extensions
        )
        self.template = template

    @tornado.web.authenticated
    async def post(self, path: str = ""):
        """Create a new file in the specified path.

        POST /jupyter-project/files/<parent-file-path>
            Creates a new file applying the parameters to the Jinja template.

        Request json body:
            Dictionary of parameters for the Jinja template.
        """
        if self.template is None:
            raise tornado.web.HTTPError(404, reason="File Jinja template not found.")

        cm = self.contents_manager
        params = self.get_json_body()

        try:
            default_name = self.default_name.render(**params)
        except TemplateError as error:
            self.log.warning(
                f"Fail to render the default name for template '{self.template.name}'"
            )
            default_name = cm.untitled_file

        ext = "".join(Path(self.template.name).suffixes)
        filename = default_name + ext
        filename = cm.increment_filename(filename, path)
        fullpath = url_path_join(path, filename)

        realpath = Path(cm.root_dir).absolute() / url2path(fullpath)
        if not realpath.parent.exists():
            realpath.parent.mkdir(parents=True)

        current_loop = tornado.ioloop.IOLoop.current()
        try:
            content = await current_loop.run_in_executor(
                None, functools.partial(self.template.render, **params)
            )
            realpath.write_text(content)
        except (OSError, TemplateError) as error:
            raise tornado.web.HTTPError(
                500,
                log_message=f"Fail to generate the file from template {self.template.name}.",
                reason=repr(error),
            )

        model = cm.get(fullpath, content=False, type="file", format="text")
        self.set_status(201)
        self.finish(json.dumps(model, default=date_default))


class ProjectsHandler(APIHandler):
    """Handler for project requests."""

    def initialize(self, template: ProjectTemplate = None):
        """Initialize request handler

        Args:
            template (ProjectTemplate): Project template object.
        """
        self.template = template

    def _get_realpath(self, path: str) -> Path:
        """Tranform notebook path to absolute path.

        Args:
            path (str): Path to be transformed

        Returns:
            Path: Absolute path
        """
        return Path(self.contents_manager.root_dir).absolute() / url2path(path)

    @tornado.web.authenticated
    async def get(self, path: str = ""):
        """Open a specific project or close any open once if path is empty.
        
        GET /jupyter-project/projects/<path-to-project>
            Open the project in the given path

            Answer json body:
                {
                    project: Project configuration file content
                }

        GET /jupyter-project/projects
            Close any opened project

            Answer json body:
                {
                    project: null
                }
        """
        if self.template is None:
            raise tornado.web.HTTPError(
                404, reason="Project cookiecutter template not found."
            )

        configuration = None
        if len(path) != 0:
            configuration = dict()
            fullpath = self._get_realpath(path)
            # Check that the path is a project
            current_loop = tornado.ioloop.IOLoop.current()
            try:
                configuration = await current_loop.run_in_executor(
                    None, self.template.get_configuration, fullpath
                )
            except (ValidationError, ValueError):
                raise tornado.web.HTTPError(
                    404, reason=f"Path {path} is not a valid project"
                )
            else:
                configuration["path"] = path

        if self.template.conda_pkgs is not None and self.template.filter_kernel:
            if len(path) == 0:
                # Close the current open project
                self.log.debug(f"[jupyter-project] Clear Kernel whitelist")
                self.kernel_spec_manager.whitelist = set()
            elif "environment" in configuration:
                kernelspecs = self.kernel_spec_manager.get_all_specs()
                kernels = {n for n, s in kernelspecs.items() if s["spec"]["metadata"].get("conda_env_name") == configuration["environment"]}
                self.log.debug(f"[jupyter-project] Set Kernel whitelist to {kernels}")
                self.kernel_spec_manager.whitelist = kernels

        self.finish(json.dumps({"project": configuration}))

    @tornado.web.authenticated
    async def post(self, path: str = ""):
        """Create a new project in the provided path.
        
        POST /jupyter-project/projects/<path-to-project>
            Create a new project in the given path

        Request json body:
            Parameters dictionary for the cookiecutter template

            Answer json body:
                {
                    project: Project configuration file content
                }
        """
        if self.template is None:
            raise tornado.web.HTTPError(
                404, reason="Project cookiecutter template not found."
            )

        params = self.get_json_body()

        realpath = self._get_realpath(path)
        if not realpath.parent.exists():
            realpath.parent.mkdir(parents=True)

        current_loop = tornado.ioloop.IOLoop.current()
        try:
            folder_name, configuration = await current_loop.run_in_executor(
                None, self.template.render, params, realpath
            )
        except (CookiecutterException, OSError, ValueError) as error:
            raise tornado.web.HTTPError(
                500,
                log_message=f"Fail to generate the project from the cookiecutter template.",
                reason=repr(error),
            )
        except ValidationError as error:
            raise tornado.web.HTTPError(
                500,
                log_message=f"Invalid default project configuration file.",
                reason=repr(error),
            )
        else:
            configuration["path"] = url_path_join(path, folder_name)

        self.set_status(201)
        self.finish(json.dumps({"project": configuration}))

    @tornado.web.authenticated
    async def delete(self, path: str = ""):
        """Delete the project at the given path.
        
        DELETE /jupyter-project/projects/<path-to-project>
            Delete the project
        """
        if self.template is None:
            raise tornado.web.HTTPError(
                404, reason="Project cookiecutter template not found."
            )

        if len(path) == 0:
            self.finish(b"{}")
            return

        fullpath = self._get_realpath(path)
        # Check that the path is a project
        current_loop = tornado.ioloop.IOLoop.current()
        try:
            await current_loop.run_in_executor(
                None, self.template.get_configuration, fullpath
            )
        except (ValidationError, ValueError):
            raise tornado.web.HTTPError(
                404, reason=f"Path {path} is not a valid project"
            )

        rmtree(fullpath, ignore_errors=True)

        self.set_status(204)


class SettingsHandler(APIHandler):
    """Handler to get the extension server configuration."""

    def initialize(self, project_settings: Dict[str, Any] = None):
        self.project_settings = project_settings or {}

    @tornado.web.authenticated
    def get(self):
        """Get the server extension settings.

        Return body:
        {
            fileTemplates: [
                {
                    destination: str | null,
                    endpoint: str,
                    icon: str | null,
                    name: str,
                    schema: JSONschema | null
                }
            ],
            projectTemplate: {
                configurationFilename: str,
                defaultCondaPackages: str | null,
                defaultPath: str | null,
                editableInstall: bool,
                schema: JSONschema | null,
                withGit: bool
            }
        }
        """
        self.finish(json.dumps(self.project_settings))


def setup_handlers(
    web_app: "NotebookWebApplication", config: JupyterProject, logger: logging.Logger
):

    host_pattern = ".*$"

    base_url = url_path_join(web_app.settings["base_url"], NAMESPACE)
    handlers = list()

    # File templates
    list_templates = config.file_templates
    ## Create the loaders
    templates = dict()
    for template in list_templates:
        name = template.name
        if name in templates:
            logger.warning(f"Template '{name}' already exists; it will be ignored.")
            continue
        else:
            new_template = {
                "loader": None,
                "files": template.files,
            }
            location = Path(template.location)
            if location.exists() and location.is_dir():
                new_template["loader"] = FileSystemLoader(str(location))
            elif len(template.module) > 0:
                try:
                    new_template["loader"] = PackageLoader(
                        template.module, package_path=str(location)
                    )
                except ModuleNotFoundError:
                    logger.warning(f"Unable to find module '{template.module}'")

            if new_template["loader"] is None:
                logger.warning(f"Unable to load templates '{name}'.")
                continue

            templates[name] = new_template

    env = Environment(
        loader=PrefixLoader({name: t["loader"] for name, t in templates.items()}),
        extensions=jinja2_extensions,
    )

    ## Create the handlers
    file_settings = list()
    for name, template in templates.items():
        filenames = set()
        for file in template["files"]:
            pfile = Path(file.template)
            suffixes = "".join(pfile.suffixes)
            short_name = pfile.as_posix()[: -(len(suffixes))]
            if short_name in filenames:
                logger.warning(
                    f"Template '{name}/{pfile.as_posix()}' skipped as it has the same name than another template."
                )
                continue
            filenames.add(short_name)

            endpoint = quote("/".join((name, short_name)), safe="")
            handlers.append(
                (
                    url_path_join(
                        base_url, r"files/{:s}{:s}".format(endpoint, path_regex),
                    ),
                    FileTemplatesHandler,
                    {
                        "default_name": file.default_name,
                        "template": env.get_template(f"{name}/{pfile.as_posix()}"),
                    },
                )
            )

            destination = (
                None if file.destination == Path("") else file.destination.as_posix()
            )

            file_settings.append(
                {
                    "name": file.template_name or endpoint,
                    "endpoint": endpoint,
                    "destination": destination,
                    "icon": file.icon,
                    "schema": file.schema if len(file.schema) else None,
                }
            )

    project_template = config.project_template
    if project_template is None or project_template.template is None:
        project_settings = None
    else:
        handlers.append(
            (
                url_path_join(base_url, r"projects{:s}".format(path_regex)),
                ProjectsHandler,
                {"template": project_template},
            )
        )

        default_path = (
            None
            if project_template.default_path == Path("")
            else project_template.default_path.as_posix()
        )
        project_settings = {
            "configurationFilename": project_template.configuration_filename,
            "defaultCondaPackages": project_template.conda_pkgs,
            "defaultPath": default_path,
            "editableInstall": project_template.editable_install,
            "schema": (
                project_template.schema if len(project_template.schema) else None
            ),
            "withGit": True,  # TODO make it configurable
        }

    handlers.append(
        (
            url_path_join(base_url, "settings"),
            SettingsHandler,
            {
                "project_settings": {
                    "fileTemplates": file_settings,
                    "projectTemplate": project_settings,
                }
            },
        ),
    )

    web_app.add_handlers(host_pattern, handlers)
