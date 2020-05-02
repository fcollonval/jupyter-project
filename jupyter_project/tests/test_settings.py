import sys
import tempfile
from pathlib import Path
from unittest import mock
from urllib.parse import quote

import pytest
import requests
import tornado
from traitlets.config import Config

from utils import ServerTest, assert_http_error, url_path_join


template_folder = tempfile.TemporaryDirectory(suffix="settings")


class TestSettings(ServerTest):

    config = Config(
        {
            "NotebookApp": {"nbserver_extensions": {"jupyter_project": True}},
            "JupyterProject": {
                "file_templates": [
                    {
                        "name": "template1",
                        "location": str(Path(template_folder.name) / "file_templates"),
                        "files": [
                            {"template": "file1.py"},
                            {
                                "template": "file2.html",
                                "destination": "docs",
                                "schema": {"properties": {"name": {"type": "string"}}},
                            },
                        ],
                    },
                    {
                        "name": "template2",
                        "module": "my_package_settings",
                        "location": "my_templates",
                        "files": [
                            {
                                "template": "file1.py",
                                "schema": {"properties": {"count": {"type": "number"}}},
                            }
                        ],
                    },
                ],
                "project_template": {
                    "configuration_filename": "my-project.json",
                    "configuration_schema": {
                        "title": "Project configuration schema",
                        "description": "Project configuration",
                        "properties": {"n_notebooks": {"type": "number"}},
                    },
                    "default_path": "notebooks",
                    "template": "my_magic.package",
                    "schema": {
                        "title": "My Project",
                        "description": "Project template description",
                        "properties": {"count": {"type": "number"}},
                    },
                },
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

        folder = Path(template_folder.name) / "file_templates" / "my_package_settings"
        folder.mkdir(exist_ok=True, parents=True)
        sys.path.insert(0, str(folder.parent))
        folder = folder / "my_templates"

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

    def test_get_settings(self):
        answer = self.api_tester.get(["settings",])
        assert answer.status_code == 200
        settings = answer.json()
        assert settings == {
            "file_templates": [
                {
                    "endpoint": quote("/".join(("template1", "file1")), safe=""),
                    "destination": None,
                    "schema": None,
                },
                {
                    "endpoint": quote("/".join(("template1", "file2")), safe=""),
                    "destination": "docs",
                    "schema": {"properties": {"name": {"type": "string"}}},
                },
                {
                    "endpoint": quote("/".join(("template2", "file1")), safe=""),
                    "destination": None,
                    "schema": {"properties": {"count": {"type": "number"}}},
                },
            ],
            "project_template": {
                "configuration_filename": "my-project.json",
                "default_path": "notebooks",
                "schema": {
                    "title": "My Project",
                    "description": "Project template description",
                    "properties": {"count": {"type": "number"}},
                },
            },
        }


class TestEmptySettings(ServerTest):

    config = Config(
        {
            "NotebookApp": {"nbserver_extensions": {"jupyter_project": True}}
        }
    )

    def test_get_empty_settings(self):
        answer = self.api_tester.get(["settings",])
        assert answer.status_code == 200
        settings = answer.json()
        assert settings == {"file_templates": [], "project_template": None}

    def test_no_project_endpoint(self):
        with assert_http_error(404):
            self.api_tester.get(["projects"])

        with assert_http_error(404):
            self.api_tester.post(["projects"])

        with assert_http_error(404):
            self.api_tester.delete(["projects"])
