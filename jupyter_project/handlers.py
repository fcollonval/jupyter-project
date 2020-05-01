import functools
import json
from pathlib import Path
from shutil import rmtree
from urllib.parse import quote

from jinja2 import (
    Environment,
    FileSystemLoader,
    PackageLoader,
    PrefixLoader,
    Template,
    TemplateError,
)
from jupyter_client.jsonutil import date_default
from notebook.base.handlers import APIHandler, path_regex
from notebook.utils import url_path_join, url2path
import tornado

from .config import JupyterProject

NAMESPACE = "jupyter-project"


class ConfigHandler(APIHandler):
    def initialize(self, config: JupyterProject = None):
        self.config = config

    @tornado.web.authenticated
    async def get(self):
        self.log.debug(f"GET /{NAMESPACE}/config")
        self.finish(json.dumps({}))


class JProjectHandler(APIHandler):
    def _get_realpath(self, path: str) -> Path:
        """Tranform notebook path to absolute path.

        Args:
            path (str): Path to be transformed

        Returns:
            Path: Absolute path
        """
        return Path(self.contents_manager.root_dir) / url2path(path)


class ProjectsHandler(JProjectHandler):
    def initialize(self, template: str = ""):
        """Initialize request handler

        Parameters
        ----------
        template : str
            Folder containing the cookiecutter template to be used to generate a CoSApp project.
        """
        self.template = template

    @tornado.web.authenticated
    async def get(self, path: str = ""):
        self.log.debug(f"GET /{NAMESPACE}/projects{path}")
        self.finish(json.dumps({}))

    @tornado.web.authenticated
    async def post(self, path: str = ""):
        self.log.debug(f"POST /{NAMESPACE}/projects{path}")

    @tornado.web.authenticated
    async def delete(self, path: str = ""):
        self.log.debug(f"DELETE /{NAMESPACE}/projects{path}")

        fullpath = self._get_realpath(path)
        # rmtree(fullpath, ignore_errors=True)

        # self.set_status(204)
        # self.finish()


class FileTemplatesHandler(JProjectHandler):
    def initialize(self, default_name: Template = None, template: Template = None):
        """Initialize request handler

        Parameters
        ----------
        default_name : jinja2.Template
            File default name - will be rendered with same parameters than template
        template : jinja2.Template
            Jinja2 template to use for component generation.
        """
        self.default_name = default_name or Template("Untitled")
        self.template = template

    @tornado.web.authenticated
    async def post(self, path: str = ""):
        """Create a new file in the specified path.

        POST creates a new file applying the parameters to the Jinja template.

        Request json body: dictionary of parameters for the Jinja template.
        """
        if self.template is None:
            raise tornado.web.HTTPError(404, reason="Jinja template not found.")

        cm = self.contents_manager
        root_dir = Path(cm.root_dir)
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

        realpath = root_dir / url2path(fullpath)
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


def setup_handlers(web_app: "NotebookWebApplication", config: JupyterProject, logger):

    host_pattern = ".*$"

    list_templates = config.file_templates
    project_template = config.project_template

    base_url = url_path_join(web_app.settings["base_url"], NAMESPACE)
    handlers = list()

    # File templates
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
        loader=PrefixLoader({name: t["loader"] for name, t in templates.items()})
    )

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

            endpoint = "/".join((name, short_name))
            handlers.append(
                (
                    url_path_join(
                        base_url,
                        r"files/{:s}{:s}".format(quote(endpoint, safe=""), path_regex),
                    ),
                    FileTemplatesHandler,
                    {"template": env.get_template(f"{name}/{pfile.as_posix()}")},
                )
            )

    handlers.append(
        (url_path_join(base_url, "config"), ConfigHandler, {"config": config}),
    )
    handlers.append(
        (
            url_path_join(base_url, r"projects{:s}".format(path_regex)),
            ProjectsHandler,
            {"template": project_template},
        )
    )
    web_app.add_handlers(host_pattern, handlers)