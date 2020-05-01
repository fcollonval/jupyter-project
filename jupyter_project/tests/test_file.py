import os
import re
import sys
import tempfile
import uuid
from pathlib import Path
from unittest import mock
from urllib.parse import quote

import jinja2
import pytest
import requests
import tornado
from traitlets.config import Config

from utils import ServerTest, assert_http_error, url_path_join

template_folder = tempfile.TemporaryDirectory(suffix="files")


def generate_path():
    return url_path_join(*str(uuid.uuid4()).split("-"))


class TestPathFileTemplate(ServerTest):

    config = Config(
        {
            "NotebookApp": {"nbserver_extensions": {"jupyter_project": True}},
            "JupyterProject": {
                "file_templates": [
                    {
                        "name": "template1",
                        "location": str(Path(template_folder.name) / "file_templates"),
                        "files": [{"template": "file1.py"}, {"template": "file2.html"}],
                    },
                    {
                        "name": "template2",
                        "module": "my_package",
                        "location": "my_templates",
                        "files": [{"template": "file1.py"}],
                    },
                    {
                        "name": "template3",
                        "module": "my_package.sub",
                        "location": "templates",
                        "files": [{"template": "file1.py"}],
                    },
                ]
            },
        }
    )

    @classmethod
    def setup_class(cls):
        # Given
        folder = Path(template_folder.name) / "file_templates"
        folder.mkdir(exist_ok=True, parents=True)
        file1 = folder / "file1.py"
        file1.write_text("def add(a, b):\n    return a + b\n")
        file2 = folder / "file2.html"
        file2.write_text(
            """<!doctype html>
<html lang="en">
<head>
  <title>HTML</title>
</head>
<body>
</body>
</html>"""
        )

        folder = Path(template_folder.name) / "file_templates" / "my_package"
        folder.mkdir(exist_ok=True, parents=True)
        sys.path.insert(0, str(folder.parent))
        folder1 = folder / "my_templates"
        folder2 = folder / "sub" / "templates"

        for folder in (folder1, folder2):
            folder.mkdir(exist_ok=True, parents=True)
            init = folder.parent / "__init__.py"
            init.write_bytes(b"")
            file1 = folder / "file1.py"
            file1.write_text("def add(a, b):\n    return a + b\n")
        super().setup_class()

    @classmethod
    def teardown_class(cls):
        super().teardown_class()
        sys.path.remove(str(Path(template_folder.name) / "file_templates"))
        template_folder.cleanup()

    @mock.patch("jupyter_project.handlers.Template")
    @mock.patch("jinja2.Template.render")
    def test_template1_file1(self, renderer, default_name):
        instance = default_name.return_value
        name = str(uuid.uuid4())
        instance.render.return_value = name
        renderer.return_value = "dummy content"
        path = generate_path()
        body = dict(dummy="hello", smart="world")

        answer = self.api_tester.post(["files", quote("template1/file1", safe=""), path], body=body)
        assert answer.status_code == 201

        instance.render.assert_called_with(**body)
        renderer.assert_called_with(**body)
        model = answer.json()
        assert model['content'] is None
        assert model['name'] == name + ".py"
        assert model['path'] == url_path_join(path, name + ".py")

    @mock.patch("jupyter_project.handlers.Template")
    @mock.patch("jinja2.Template.render")
    def test_template1_file2(self, renderer, default_name):
        instance = default_name.return_value
        name = str(uuid.uuid4())
        instance.render.return_value = name
        renderer.return_value = "dummy content"
        path = generate_path()
        body = dict(dummy="hello", smart="world")

        answer = self.api_tester.post(["files", quote("template1/file2", safe=""), path], body=body)
        assert answer.status_code == 201

        instance.render.assert_called_with(**body)
        renderer.assert_called_with(**body)
        model = answer.json()
        assert model['content'] is None
        assert model['name'] == name + ".html"
        assert model['path'] == url_path_join(path, name + ".html")
        
    @mock.patch("jupyter_project.handlers.Template")
    @mock.patch("jinja2.Template.render")
    def test_template2_file1(self, renderer, default_name):
        instance = default_name.return_value
        name = str(uuid.uuid4())
        instance.render.return_value = name
        renderer.return_value = "dummy content"
        path = generate_path()
        body = dict(dummy="hello", smart="world")
        
        answer = self.api_tester.post(["files", quote("template2/file1", safe=""), path], body=body)
        assert answer.status_code == 201

        instance.render.assert_called_with(**body)
        renderer.assert_called_with(**body)
        model = answer.json()
        assert model['content'] is None
        assert model['name'] == name + ".py"
        assert model['path'] == url_path_join(path, name + ".py")

    @mock.patch("jupyter_project.handlers.Template")
    @mock.patch("jinja2.Template.render")
    def test_template3_file1(self, renderer, default_name):
        instance = default_name.return_value
        name = str(uuid.uuid4())
        instance.render.return_value = name
        renderer.return_value = "dummy content"
        path = generate_path()
        body = dict(dummy="hello", smart="world")
        
        answer = self.api_tester.post(["files", quote("template3/file1", safe=""), path], body=body)
        assert answer.status_code == 201

        instance.render.assert_called_with(**body)
        renderer.assert_called_with(**body)
        model = answer.json()
        assert model['content'] is None
        assert model['name'] == name + ".py"
        assert model['path'] == url_path_join(path, name + ".py")

    def test_missing_endpoint(self):
        with pytest.raises(requests.exceptions.HTTPError):
            self.api_tester.post(["files", quote("template4/file", safe="")], body={})

    def test_missing_body(self):
        with pytest.raises(requests.exceptions.HTTPError):
            self.api_tester.post(["files", quote("template3/file1", safe="")])

    @mock.patch("jupyter_project.handlers.Template")
    @mock.patch("jinja2.Template.render")
    def test_fail_name_rendering(self, renderer, default_name):
        instance = default_name.return_value
        instance.render.side_effect = jinja2.TemplateError
        renderer.return_value = "dummy content"
        path = generate_path()
        body = dict(dummy="hello", smart="world")

        answer = self.api_tester.post(["files", quote("template1/file1", safe=""), path], body=body)
        assert answer.status_code == 201

        instance.render.assert_called_with(**body)
        renderer.assert_called_with(**body)
        model = answer.json()
        assert model['content'] is None
        print(model['name'])
        assert re.match(r"untitled\d*\.py", model['name']) is not None
        assert re.match(path + r"/untitled\d*\.py", model['path']) is not None

    @mock.patch("jupyter_project.handlers.Template")
    @mock.patch("jinja2.Template.render")
    def test_fail_template_rendering(self, renderer, default_name):
        instance = default_name.return_value
        name = str(uuid.uuid4())
        instance.render.return_value = name
        renderer.side_effect = jinja2.TemplateError
        path = generate_path()
        body = dict(dummy="hello", smart="world")

        with pytest.raises(requests.exceptions.HTTPError):
            self.api_tester.post(["files", quote("template1/file1", safe=""), path], body=body)
