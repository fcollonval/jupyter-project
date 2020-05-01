import pytest
from traitlets import TraitError
from traitlets.config import Config

from jupyter_project.config import FileTemplateLoader, JupyterProject, ProjectTemplate


@pytest.mark.parametrize(
    "config, files, pfile, ptemplate",
    [
        (
            {},
            [],
            "jupyter-project.json",
            dict(
                name="drivendata",
                template="https://github.com/drivendata/cookiecutter-data-science",
            ),
        ),
        (
            {
                "file_templates": [
                    {
                        "name": "template1",
                        "location": "/dummy/file_templates",
                        "files": [{"template": "template1.py"}],
                    }
                ]
            },
            [
                dict(
                    name="template1",
                    location="/dummy/file_templates",
                    files=[dict(template="template1.py",)],
                )
            ],
            "jupyter-project.json",
            dict(
                name="drivendata",
                template="https://github.com/drivendata/cookiecutter-data-science",
                schema=dict(),
                destination=".",
            ),
        ),
        (
            {
                "file_templates": [
                    {
                        "location": "/dummy/file_templates",
                        "files": [{"template": "template1.py"}],
                    }
                ]
            },
            TraitError,
            None,
            None,
        ),
        (
            {
                "file_templates": [
                    {"name": "template1", "files": [{"template": "template1.py"}]}
                ]
            },
            TraitError,
            None,
            None,
        ),
        (
            {
                "file_templates": [
                    {"name": "template1", "location": "/dummy/file_templates"}
                ]
            },
            TraitError,
            None,
            None,
        ),
        (
            {
                "file_templates": [
                    {
                        "name": "template1",
                        "location": "/dummy/file_templates",
                        "files": [
                            {
                                "template": "template1.py",
                                "schema": dict(
                                    title="schema", description="empty schema"
                                ),
                                "default_name": "new_file",
                                "destination": "star_folder",
                            }
                        ],
                    }
                ]
            },
            [
                dict(
                    name="template1",
                    location="/dummy/file_templates",
                    files=[
                        dict(
                            template="template1.py",
                            schema=dict(title="schema", description="empty schema"),
                            default_name="new_file",
                            destination="star_folder",
                        )
                    ],
                )
            ],
            "jupyter-project.json",
            dict(
                name="drivendata",
                template="https://github.com/drivendata/cookiecutter-data-science",
                schema=dict(),
                destination=".",
            ),
        ),
        (
            {"project_file": "my-project.json"},
            [],
            "my-project.json",
            dict(
                name="drivendata",
                template="https://github.com/drivendata/cookiecutter-data-science",
                schema=dict(),
                destination=".",
            ),
        ),
        (
            {
                "project_file": "my-project.json",
                "project_template": {
                    "name": "my-project-template",
                    "template": "my_magic.package",
                },
            },
            [],
            "my-project.json",
            dict(
                name="my-project-template",
                template="my_magic.package",
                schema=dict(),
                destination=".",
            ),
        ),
        (
            {"project_template": {"template": "my_magic.package",},},
            TraitError,
            None,
            None,
        ),
        (
            {"project_template": {"name": "my-project-template",},},
            TraitError,
            None,
            None,
        ),
        (
            {
                "project_file": "my-project.json",
                "project_template": {
                    "name": "my-project-template",
                    "template": "my_magic.package",
                    "destination": "my_workspace",
                    "schema": dict(
                        title="Project parameters",
                        description="My project template parameters",
                    ),
                },
            },
            [],
            "my-project.json",
            dict(
                name="my-project-template",
                template="my_magic.package",
                schema=dict(
                    title="Project parameters",
                    description="My project template parameters",
                ),
                destination="my_workspace",
            ),
        ),
    ],
)
def test_JupyterProject(config, files, pfile, ptemplate):
    if isinstance(files, type) and issubclass(files, Exception):
        with pytest.raises(files):
            jp = JupyterProject(
                config=Config(
                    {
                        "NotebookApp": {
                            "nbserver_extensions": {"jupyter_project": True}
                        },
                        "JupyterProject": config,
                    }
                )
            )
    else:
        jp = JupyterProject(
            config=Config(
                {
                    "NotebookApp": {"nbserver_extensions": {"jupyter_project": True}},
                    "JupyterProject": config,
                }
            )
        )

        assert jp.file_templates == [FileTemplateLoader(**kw) for kw in files]
        assert jp.project_file == pfile
        assert jp.project_template == ProjectTemplate(**ptemplate)
