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

template_folder = tempfile.TemporaryDirectory(suffix="project")


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
    ),
)
def test_ProjectTemplate_render(tmp_path, kwargs):
    tpl = ProjectTemplate(**kwargs)
    params = dict(key1=22, key2="hello darling")
    with mock.patch("jupyter_project.project.cookiecutter") as cookiecutter:
        configuration = tpl.render(params, tmp_path)

    assert configuration == dict()
    if tpl.template is not None:
        cookiecutter.assert_called_once_with(
            tpl.template, no_input=True, extra_context=params, output_dir=str(tmp_path)
        )
        
        if len(tpl.configuration_filename) > 0:
            (tmp_path / tpl.configuration_filename).exists()

    else:
        cookiecutter.assert_not_called()
        assert not (tmp_path / tpl.configuration_filename).exists()


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

    @classmethod
    def setup_class(cls):
        # Given
        folder = Path(template_folder.name) / "project_template" / "my_magic" / "package" / "my-project-template"
        folder.mkdir(exist_ok=True, parents=True)
        parent = folder.parent
        for i in range(2):
            init = parent / "__init__.py"
            init.write_bytes(b"")
            parent = parent.parent

        sys.path.insert(0, str(parent))
        super().setup_class()

    @classmethod
    def teardown_class(cls):
        super().teardown_class()
        sys.path.remove(str(Path(template_folder.name) / "project_template"))
        template_folder.cleanup()

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
