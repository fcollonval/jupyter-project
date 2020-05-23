import pytest
from traitlets import TraitError
from traitlets.config import Config

from jupyter_project.config import FileTemplateLoader, JupyterProject, ProjectTemplate


@pytest.mark.parametrize(
    "config, files, ptemplate",
    [
        ({}, [], None,),
        (
            {
                "file_templates": [
                    {
                        "name": "template1",
                        "location": "/dummy/file_templates",
                        "files": [{"template": "template1.py"}],
                    }
                ],
            },
            [
                dict(
                    name="template1",
                    location="/dummy/file_templates",
                    files=[dict(template="template1.py",)],
                )
            ],
            None,
        ),
        (
            {
                "file_templates": [
                    {
                        "location": "/dummy/file_templates",
                        "files": [{"template": "template1.py"}],
                    }
                ],
            },
            TraitError,
            None,
        ),
        (
            {
                "file_templates": [
                    {"name": "template1", "files": [{"template": "template1.py"}]}
                ],
            },
            TraitError,
            None,
        ),
        (
            {
                "file_templates": [
                    {"name": "template1", "location": "/dummy/file_templates"}
                ],
            },
            TraitError,
            None,
        ),
        (
            {
                "file_templates": [
                    {
                        "name": "template1",
                        "location": "/dummy/file_templates",
                        "files": [],
                    }
                ],
            },
            TraitError,
            None,
        ),
        (
            {
                "file_templates": [
                    {
                        "name": "template1",
                        "location": "/dummy/file_templates",
                        "files": [{"template": ""}],
                    }
                ],
            },
            TraitError,
            None,
        ),
        (
            {
                "file_templates": [
                    {
                        "name": "template1",
                        "location": "/dummy/file_templates",
                        "files": [{"default_name": "", "template": "template1.py"}],
                    }
                ],
            },
            TraitError,
            None,
        ),
        (
            {
                "file_templates": [
                    {
                        "name": "template1",
                        "location": "/dummy/file_templates",
                        "files": [
                            {"template": "template1.py", "template_name": 24}
                        ],
                    }
                ],
            },
            TraitError,
            None,
        ),
        (
            {
                "file_templates": [
                    {
                        "name": "template1",
                        "location": "/dummy/file_templates",
                        "files": [
                            {"template": "template1.py", "icon": "<notsvg></svg>"}
                        ],
                    }
                ],
            },
            TraitError,
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
                                "template_name": "My beautiful template",
                                "schema": dict(
                                    title="schema", description="empty schema"
                                ),
                                "default_name": "new_file",
                                "destination": "star_folder",
                                "icon": '<svg viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg"><rect width="100" height="100" /></svg>',
                            }
                        ],
                    }
                ],
            },
            [
                dict(
                    name="template1",
                    location="/dummy/file_templates",
                    files=[
                        dict(
                            template="template1.py",
                            template_name="My beautiful template",
                            schema=dict(title="schema", description="empty schema"),
                            default_name="new_file",
                            destination="star_folder",
                            icon='<svg viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg"><rect width="100" height="100" /></svg>',
                        )
                    ],
                )
            ],
            None,
        ),
        (
            {
                "project_template": {
                    "template": "my_magic.package",
                    "configuration_filename": "my-project.json",
                }
            },
            [],
            dict(
                template="my_magic.package", configuration_filename="my-project.json",
            ),
        ),
        (
            {
                "project_template": {
                    "template": "my_magic.package",
                    "configuration_schema": dict(
                        title="schema", description="empty schema"
                    ),
                }
            },
            [],
            dict(
                template="my_magic.package",
                configuration_schema=dict(title="schema", description="empty schema"),
            ),
        ),
        (
            {
                "project_template": {
                    "template": "my_magic.package",
                    "default_path": "my-project.json",
                }
            },
            [],
            dict(template="my_magic.package", default_path="my-project.json",),
        ),
        (
            {
                "project_template": {
                    "template": "my_magic.package",
                    "schema": dict(title="schema", description="empty schema"),
                }
            },
            [],
            dict(
                template="my_magic.package",
                schema=dict(title="schema", description="empty schema"),
            ),
        ),
        (
            {"project_template": {"template": "my_magic.package",},},
            [],
            dict(template="my_magic.package",),
        ),
        ({"project_template": {"template": "",},}, TraitError, None,),
        ({"project_template": {"template": "my_magic.package", "folder_name": ""},}, TraitError, None,),
        (
            {
                "project_template": {
                    "configuration_filename": "my-project.json",
                    "configuration_schema": dict(
                        title="Project configuration",
                        description="My project configuration structure",
                    ),
                    "conda_pkgs": "Python 3",
                    "default_path": "my_workspace",
                    "editable_install": False,
                    "folder_name": "banana",
                    "template": "my_magic.package",
                    "schema": dict(
                        title="Project parameters",
                        description="My project template parameters",
                    ),
                },
            },
            [],
            dict(
                configuration_filename="my-project.json",
                configuration_schema=dict(
                    title="Project configuration",
                    description="My project configuration structure",
                ),
                conda_pkgs="Python 3",
                default_path="my_workspace",
                editable_install=False,
                folder_name="banana",
                template="my_magic.package",
                schema=dict(
                    title="Project parameters",
                    description="My project template parameters",
                ),
            ),
        ),
    ],
)
def test_JupyterProject(config, files, ptemplate):
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
        if ptemplate is None:
            assert jp.project_template is None
        else:
            assert jp.project_template == ProjectTemplate(**ptemplate)
