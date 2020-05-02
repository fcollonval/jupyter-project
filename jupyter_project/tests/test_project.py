import json
import os
import re
import sys
import tempfile
import uuid
from pathlib import Path
from unittest import mock
from urllib.parse import quote

import jsonschema
import pytest
import tornado
from cookiecutter.exceptions import CookiecutterException
from traitlets import TraitError
from traitlets.config import Config

from jupyter_project.project import ProjectTemplate
from utils import ServerTest, assert_http_error, url_path_join, generate_path


@pytest.mark.parametrize("kwargs, exception", [(dict(template=""), TraitError)])
def test_ProjectTemplate_constructor(kwargs, exception):
    with pytest.raises(exception):
        ProjectTemplate(**kwargs)


@pytest.mark.parametrize(
    "kwargs, configuration, exception",
    (
        (dict(), dict(), None),
        (dict(template="https://github.com/me/my-template",), dict(), ValueError),
        (
            dict(template="https://github.com/me/my-template",),
            dict(key1=1, key2="banana"),
            None,
        ),
        (
            dict(
                template="https://github.com/me/my-template",
                configuration_schema={
                    "type": "object",
                    "properties": {
                        "key1": {"type": "number"},
                        "key2": {"type": "string", "minLength": 3},
                    },
                },
            ),
            dict(key1=1, key2="banana"),
            None,
        ),
        (
            dict(
                template="https://github.com/me/my-template",
                configuration_schema={
                    "type": "object",
                    "properties": {
                        "key1": {"type": "number"},
                        "key2": {"type": "string", "minLength": 8},
                    },
                },
            ),
            dict(key1=1, key2="banana"),
            jsonschema.ValidationError,
        ),
    ),
)
def test_ProjectTemplate_get_configuration(tmp_path, kwargs, configuration, exception):
    tpl = ProjectTemplate(**kwargs)
    if configuration:
        (tmp_path / tpl.configuration_filename).write_text(json.dumps(configuration))

    if exception is None:
        assert configuration == tpl.get_configuration(tmp_path)
    else:
        with pytest.raises(exception):
            tpl.get_configuration(tmp_path)


@pytest.mark.parametrize(
    "kwargs",
    (
        dict(),
        dict(template=None),
        dict(template="https://github.com/me/my-template"),
        dict(template="https://github.com/me/my-template", configuration_filename=""),
        dict(module="my_magic.package", template="my-project-template"),
    ),
)
def test_ProjectTemplate_render(tmp_path, kwargs):
    if "module" in kwargs:
        folder = tmp_path / "project_template" / "my_magic" / "package" / kwargs["template"]
        folder.mkdir(exist_ok=True, parents=True)
        parent = folder.parent
        for i in range(2):
            init = parent / "__init__.py"
            init.write_bytes(b"")
            parent = parent.parent

        sys.path.insert(0, str(parent))
        template_uri = str(folder)
    else:
        parent = None
        template_uri = kwargs.get("template", None)

    try:
        tpl = ProjectTemplate(**kwargs)
        params = dict(key1=22, key2="hello darling")
        with mock.patch("jupyter_project.project.cookiecutter") as cookiecutter:
            configuration = tpl.render(params, tmp_path)

        assert configuration == dict()
        if template_uri is not None:
            cookiecutter.assert_called_once_with(
                template_uri, no_input=True, extra_context=params, output_dir=str(tmp_path)
            )
            
            if len(tpl.configuration_filename) > 0:
                (tmp_path / tpl.configuration_filename).exists()

        else:
            cookiecutter.assert_not_called()
            assert not (tmp_path / tpl.configuration_filename).exists()

    finally:
        if parent is not None:
            sys.path.remove(str(parent))

class TestProjectTemplate(ServerTest):

    config = Config(
        {
            "NotebookApp": {"nbserver_extensions": {"jupyter_project": True}},
            "JupyterProject": {
                "project_template": {
                    "configuration_filename": "my-project.json",
                    "module": "my_magic.package",
                    "template": "my-project-template",
                    "schema": {
                        "title": "My Project",
                        "description": "Project template description",
                        "type": "object",
                        "properties": {"count": {"type": "number"}},
                    },
                },
            },
        }
    )

    def test_project_get(self):
        path = generate_path()
        configuration = dict(key1=22, key2="hello darling")

        with mock.patch("jupyter_project.handlers.ProjectTemplate.get_configuration") as mock_configuration:
            mock_configuration.return_value = configuration

            answer = self.api_tester.get(["projects", path])
            assert answer.status_code == 200
            conf = answer.json()
            assert conf == configuration

        mock_configuration.assert_called_once_with(Path(self.notebook_dir) / path)

    def test_project_get_no_path(self):
        answer = self.api_tester.get(["projects", ])
        assert answer.status_code == 200
        conf = answer.json()
        assert conf == dict()

    def test_project_get_no_configuration(self):
        path = generate_path()

        with mock.patch("jupyter_project.handlers.ProjectTemplate.get_configuration") as mock_configuration:
            mock_configuration.side_effect = ValueError

            with assert_http_error(404):
                self.api_tester.get(["projects", path])

        mock_configuration.assert_called_once_with(Path(self.notebook_dir) / path)

    def test_project_get_invalid_configuration(self):
        path = generate_path()

        with mock.patch("jupyter_project.handlers.ProjectTemplate.get_configuration") as mock_configuration:
            mock_configuration.side_effect = jsonschema.ValidationError(message="failure")

            with assert_http_error(404):
                self.api_tester.get(["projects", path])

        mock_configuration.assert_called_once_with(Path(self.notebook_dir) / path)

    def test_project_post(self):
        path = generate_path()
        body = dict(dummy="hello", smart="world")
        configuration = dict(key1=22, key2="hello darling")

        with mock.patch("jupyter_project.handlers.ProjectTemplate.render") as mock_render:
            mock_render.return_value = configuration
            answer = self.api_tester.post(
                ["projects", path], body=body
            )
            assert answer.status_code == 201

            config = answer.json()
            assert config == configuration

        mock_render.assert_called_once_with(body, Path(self.notebook_dir) / path)

    def test_project_post_cookiecutter_failure(self):
        path = generate_path()
        body = dict(dummy="hello", smart="world")

        with mock.patch("jupyter_project.handlers.ProjectTemplate.render") as mock_render:
            mock_render.side_effect = CookiecutterException

            with assert_http_error(500):
                self.api_tester.post(["projects", path], body=body)

        mock_render.assert_called_once_with(body, Path(self.notebook_dir) / path)

    def test_project_post_invalid_configuration(self):
        path = generate_path()
        body = dict(dummy="hello", smart="world")

        with mock.patch("jupyter_project.project.ProjectTemplate.render") as mock_render:
            mock_render.side_effect = jsonschema.ValidationError(message="failure")

            with assert_http_error(500):
                self.api_tester.post(["projects", path], body=body)

        mock_render.assert_called_once_with(body, Path(self.notebook_dir) / path)

    def test_project_delete(self):
        path = generate_path()

        with mock.patch("jupyter_project.project.ProjectTemplate.get_configuration") as mock_configuration:
            with mock.patch("jupyter_project.handlers.rmtree") as mock_rmtree:
                answer = self.api_tester.delete(["projects", path])
                assert answer.status_code == 204
                assert answer.text == ""

        mock_rmtree.assert_called_once_with(Path(self.notebook_dir) / path, ignore_errors=True)

    def test_project_delete_empty_path(self):
        answer = self.api_tester.delete(["projects", ])
        assert answer.status_code == 200
        assert answer.text == ""

    def test_project_delete_no_configuration(self):
        path = generate_path()

        with mock.patch("jupyter_project.project.ProjectTemplate.get_configuration") as mock_configuration:
            with mock.patch("jupyter_project.handlers.rmtree") as mock_rmtree:
                mock_configuration.side_effect = ValueError

                with assert_http_error(404):
                    self.api_tester.delete(["projects", path])

        mock_configuration.assert_called_once_with(Path(self.notebook_dir) / path)

    def test_project_delete_invalid_configuration(self):
        path = generate_path()

        with mock.patch("jupyter_project.project.ProjectTemplate.get_configuration") as mock_configuration:
            with mock.patch("jupyter_project.handlers.rmtree") as mock_rmtree:
                mock_configuration.side_effect = jsonschema.ValidationError(message="failure")

                with assert_http_error(404):
                    self.api_tester.delete(["projects", path])

        mock_configuration.assert_called_once_with(Path(self.notebook_dir) / path)
