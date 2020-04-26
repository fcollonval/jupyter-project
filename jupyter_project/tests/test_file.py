import os
import sys
import tempfile
from pathlib import Path
from urllib.parse import quote

import pytest
import requests
import tornado
from traitlets.config import Config

from utils import ServerTest, assert_http_error

template_folder = tempfile.TemporaryDirectory()


class TestPathFileTemplate(ServerTest):

    config = Config(
        {
            "NotebookApp": {"nbserver_extensions": {"jupyter_project": True}},
            "JupyterProject": {
                "file_templates": [
                    {
                        "name": "template1",
                        "template": str(Path(template_folder.name) / "file_templates"),
                        "files": ["file1.py", "file2.html"],
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
        super().setup_class()

    @classmethod
    def teardown_class(cls):
        super().teardown_class()
        template_folder.cleanup()

    def test_filesystem_template(self):

        # When
        tpl1 = self.api_tester.post([quote("template1/file1", safe="")])
        tpl2 = self.api_tester.post([quote("template1/file2", safe="")])

        # Then

        with pytest.raises(requests.exceptions.HTTPError):
            self.api_tester.post(["template3"])


class TestPackageFileTemplate(ServerTest):

    config = Config(
        {
            "NotebookApp": {"nbserver_extensions": {"jupyter_project": True}},
            "JupyterProject": {
                "file_templates": [
                    {
                        "name": "template1",
                        "module": "my_package",
                        "template": "my_templates",
                        "files": ["file1.py"],
                    },
                    {
                        "name": "template2",
                        "module": "my_package.sub",
                        "template": "templates",
                        "files": ["file1.py"],
                    },
                ]
            },
        }
    )

    @classmethod
    def setup_class(cls):
        # Given
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
        template_folder.cleanup()

    def test_package_template(self):
        # When
        tpl1 = self.api_tester.post([quote("template1/file1", safe="")])
        tpl2 = self.api_tester.post([quote("template2/file1", safe="")])

        # Then

        with pytest.raises(requests.exceptions.HTTPError):
            self.api_tester.post(["template3"])
