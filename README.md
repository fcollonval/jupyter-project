# jupyter-project

[![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/fcollonval/jupyter-project/with-conda?urlpath=lab)
[![Github Actions Status](https://github.com/fcollonval/jupyter-project/workflows/Test/badge.svg)](https://github.com/fcollonval/jupyter-project/actions?query=workflow%3ATest)
[![Coverage Status](https://coveralls.io/repos/github/fcollonval/jupyter-project/badge.svg?branch=master)](https://coveralls.io/github/fcollonval/jupyter-project?branch=master)
[![Conda (channel only)](https://img.shields.io/conda/vn/conda-forge/jupyter-project)](https://anaconda.org/conda-forge/jupyter-project)
[![PyPI](https://img.shields.io/pypi/v/jupyter-project)](https://pypi.org/project/jupyter-project/)
[![npm](https://img.shields.io/npm/v/jupyter-project)](https://www.npmjs.com/package/jupyter-project)

An JupyterLab extension to handle (a unique) project and files templates. It adds the ability
to generate projects from a [cookiecutter](https://cookiecutter.readthedocs.io/en/latest/) template as well as generate files
from [Jinja2](https://jinja.palletsprojects.com/en/master/) templates. Those templates can be parametrized directly from
the frontend by specifying [JSON schemas](https://json-schema.org/).

This extension is composed of a Python package named `jupyter_project`
for the server extension and a NPM package named `jupyter-project`
for the frontend extension.

- [Requirements](#Requirements)
- [Install](#Install)
- [Configuration](#Configuring-the-extension)
  - [File templates](#File-templates)
  - [Project template](#Project-template)
    - [Conda integration](#Conda-environment-integration)
    - [Git integration](#Git-integration)
  - [Complete configuration](#Full-configuration)
- [Troubleshoot](#Troubleshoot)
- [Contributing](#Contributing)
- [Uninstall](#Uninstall)
- [Alternatives](#Alternatives)

## Requirements

- Python requirements:

```py
# setup.py#L63-L66

"cookiecutter",
"jinja2~=2.9",
"jsonschema",
"jupyterlab~=1.2"
```

- Optional Python requirements:

```py
# setup.py#L69-L72

"all": [
    "jupyter_conda~=3.3", 
    "jupyterlab-git>=0.10,<0.20"
],
```

- Optional JupyterLab extensions:

  - @jupyterlab/git
  - jupyterlab_conda

## Install

> Note: You will need NodeJS to install the extension.

With pip:

```bash
pip install jupyter_project
jupyter lab build
```

Or with conda:

```bash
conda install -c conda-forge jupyter_project
jupyter lab build
```

## Configuring the extension

By default, this extension will not add anything to JupyterLab as the templates must be configured
as part of the server extension configuration key **JupyterProject** (see [Jupyter server configuration](https://jupyter-notebook.readthedocs.io/en/stable/config_overview.html#) for more information).

The configuration example for Binder will be described next - this is the file [binder/jupyter_notebook_config.json](binder/jupyter_notebook_config.json).

The section for this extension must be named **JupyterProject**:

```json5
// ./binder/jupyter_notebook_config.json#L7-L7

"JupyterProject": {
```

It accepts to optional keys: _file_templates_ and _project_template_. The first defines a list
of places containing templated files. And the second describe the project template. They can
both exist alone (i.e. only file templates or only the project template).

### File templates

The file templates can be located in a `location` provided by its fullpath or in a `location`
within a Python `module`. In the Binder example, the template are located in the folder `examples`
part of the `jupyter_project` Python module:

```json5
// ./binder/jupyter_notebook_config.json#L8-L12

"file_templates": [
  {
    "name": "data-sciences",
    "module": "jupyter_project",
    "location": "examples",
```

The last parameter appearing here is _name_. It described uniquely the source of file templates.

Than comes the list of templated files available in that source. There are three templated
file examples. The shortest configuration is:

```json5
// ./binder/jupyter_notebook_config.json#L14-L16

{
  "template": "demo.ipynb"
},
```

This will create a template by copy of the provided file.

But usually, a template comes with parameters. This extension handles parameters through
a [JSON schema specification](https://json-schema.org/understanding-json-schema/index.html).
That schema will be used to prompt the user with a form that will be validated against
the schema. Then the form values will be passed to [Jinja2](https://jinja.palletsprojects.com/en/master/)
to rendered the templates.

> In addition, if a project is active, its properties like name or dirname will be available in
> the Jinja template as ``jproject.<property>`` (e.g. ``jproject.name`` for the project name).

```json5
// ./binder/jupyter_notebook_config.json#L74-L92

{
  "default_name": "{{ modelName }}",
  "destination": "src/models",
  "schema": {
    "type": "object",
    "properties": {
      "authorName": {
        "type": "string"
      },
      "modelName": {
        "type": "string",
        "pattern": "^[a-zA-Z_]\\w*$"
      }
    },
    "required": ["modelName"]
  },
  "template_name": "Train Model",
  "template": "train_model.py"
}
```

In the settings, you can see three additional entries that have not been explained yet:

- `template_name`: A nicer name for the template to be displayed in the frontend.
- `default_name`: Default name for the file generated from the template (the string may contain Jinja2 variables defined in the `schema`).
- `destination`: If you are using the project template, the generated file will be placed
  within the destination folder inside the active project folder. If no project is active
  the file will be written in the current folder. It can contain project templated variable:
  
  - ``{{jproject.name}}``: Project name
  - ``{{jproject.dirname}}``: Project directory name

The latest file template example is a complete example of all possibilities (including
type of variables that you could used in the schema):

```json5
// ./binder/jupyter_notebook_config.json#L17-L73

{
  "destination": "notebooks",
  "icon": "<svg xmlns=\"http://www.w3.org/2000/svg\" viewBox=\"0 0 16 16\"> <rect class=\"jp-icon3\" fill=\"#ffffff\" width=\"16\" height=\"16\" rx=\"2\" style=\"fill-opacity:1\" /> <path class=\"jp-icon-accent0\" fill=\"#faff00\" d=\"m 12.098275,4.7065364 -4.9999997,-0.62651 v 8.9554396 l 4.9999997,-0.32893 v -1.1 l -3.4999997,0.19305 V 8.9065364 h 1.9999997 v -1.1 l -1.9999997,-0.1 V 5.3539365 l 3.4999997,0.3526 z\" style=\"fill-opacity:1;stroke:none\" /> </svg> ",
  "template_name": "Example",
  "template": "example.ipynb",
  "schema": {
    "type": "object",
    "properties": {
      "exampleBoolean": {
        "default": false,
        "title": "A choice",
        "type": "boolean"
      },
      "exampleList": {
        "default": [1, 2, 3],
        "title": "A list of number",
        "type": "array",
        "items": {
          "default": 0,
          "type": "number"
        }
      },
      "exampleNumber": {
        "default": 42,
        "title": "A number",
        "type": "number",
        "minimum": 0,
        "maximum": 100
      },
      "exampleObject": {
        "default": {
          "number": 1,
          "street_name": "Dog",
          "street_type": "Street"
        },
        "title": "A object",
        "type": "object",
        "properties": {
          "number": { "type": "integer" },
          "street_name": { "type": "string" },
          "street_type": {
            "type": "string",
            "enum": ["Street", "Avenue", "Boulevard"]
          }
        },
        "required": ["number"]
      },
      "exampleString": {
        "default": "I_m_Beautiful",
        "title": "A string",
        "type": "string",
        "pattern": "^[a-zA-Z_]\\w*$"
      }
    },
    "required": ["exampleString"]
  }
},
```

A careful reader may notice the last available setting: `icon`. It is a stringified
svg that will be used to set a customized icon in the frontend for the template.

If you need to set templates from different sources, you can add entry similar to
`data-sciences` in the `file_templates` list.

### Project template

The second major configuration section is `project_template`. The template must
specified a value for `template` that points to a valid [cookiecutter](https://cookiecutter.readthedocs.io/en/latest/)
template source:

```json5
// ./binder/jupyter_notebook_config.json#L96-L97

"project_template": {
  "template": "https://github.com/drivendata/cookiecutter-data-science",
```

The cookiecutter template parameters that you wish the user to be able to change must be
specified as a [JSON schema](https://json-schema.org/understanding-json-schema/index.html):

```json5
// ./binder/jupyter_notebook_config.json#L98-L125

"schema": {
  "type": "object",
  "properties": {
    "project_name": {
      "type": "string",
      "default": "Project Name"
    },
    "repo_name": {
      "title": "Folder name",
      "type": "string",
      "pattern": "^[a-zA-Z_]\\w*$",
      "default": "project_name"
    },
    "author_name": {
      "type": "string",
      "description": "Your name (or your organization/company/team)"
    },
    "description": {
      "type": "string",
      "description": "A short description of the project."
    },
    "open_source_license": {
      "type": "string",
      "enum": ["MIT", "BSD-3-Clause", "No license file"]
    }
  },
  "required": ["project_name", "repo_name"]
},
```

Then you need to set `folder_name` as the name of the folder resulting from the cookiecutter
template. This is a string accepting Jinja2 variables defined in the `schema`.

The latest option in the example is `default_path`. This is optional and, if set, it should
provide the default path (folder or file) to be opened by JupyterLab once the project has
been generated. It can contain project templated variable:
  
- ``{{jproject.name}}``: Project name
- ``{{jproject.dirname}}``: Project directory name

```json5
// ./binder/jupyter_notebook_config.json#L126-L127

"folder_name": "{{ repo_name }}",
"default_path": "README.md",
```

#### Conda environment integration

If the [`jupyter_conda`](https://github.com/fcollonval/jupyter_conda) optional extension is installed
and if `conda_pkgs` is specified in the `project_template` configuration, then a Conda environment
will follow the life cycle of the project; i.e. creation of an environment at project creation,
update of the environment when opening a project and changing its packages and deletion at project deletion.

The `conda_pkgs` setting should be set to a string matching the default environment type of conda environment
to be created at project creation (see [`jupyter_conda`](https://github.com/fcollonval/jupyter_conda/blob/master/labextension/schema/plugin.json#L13)
labextension for more information). You can also set a packages list separated by space.

The binder example defines:

```json5
// ./binder/jupyter_notebook_config.json#L128-L128

"conda_pkgs": "awscli click coverage flake8 ipykernel python-dotenv>=0.5.1 sphinx"
```

> The default conda packages settings is the fallback if `environment.yml` is absent of the project
> cookiecutter template.

There are two configurable options for the project template when using the conda integration:

- `editable_install`: If True, the project folder will be installed in editable mode using `pip` in the conda environment (default: True)
- `filter_kernel`: If True, the kernel manager [whitelist](https://jupyter-notebook.readthedocs.io/en/stable/search.html?q=whitelist&check_keywords=yes&area=default)
will be set dynamically to the one of the project environment
kernel (i.e. only that kernel will be available when the project is opened) (default: True).

#### Git integration

If the [`jupyterlab-git`](https://github.com/jupyterlab/jupyterlab-git) optional extension is installed, the following features/behaviors are to be expected:

- When creating a project, it will be initialized as a git repository and a first commit with all produced files will be carried out.
- When the git HEAD changes (branch changes, pull action,...), the conda environment will be updated if the `environment.yml` file changed.

### Full configuration

Here is the description of all server extension settings:

```json
{
  "JupyterProject": {
    "file_templates": {
      "description": "List of file template loaders",
      "type": "array",
      "items": {
        "description": ,
        "type": "object",
        "properties": {
          "location": {
            "description": "Templates path",
            "type": "string"
          },
          "module": {
            "description": "Python package containing the templates 'location' [optional]",
            "type": "string"
          },
          "name": {
            "description": "Templates group name",
            "type": "string"
          },
          "files": {
            "description": "List of template files",
            "type": "array",
            "minItems": 1,
            "items": {
              "type": "object",
              "properties": {
                "default_name": {
                  "description": "Default file name (without extension; support Jinja2 templating using the schema parameters)",
                  "default": "Untitled",
                  "type": "string"
                },
                "destination": {
                  "description": "Relative destination folder [optional]",
                  "type": "string"
                },
                "icon": {
                  "description": "Template icon to display in the frontend [optional]",
                  "default": null,
                  "type": "string"
                },
                "schema": {
                  "description": "JSON schema list describing the templates parameters [optional]",
                  "type": "object"
                },
                "template": {
                  "description": "Template path",
                  "type": "string"
                },
                "template_name" : {
                  "description": "Template name in the UI [optional]",
                  "type": "string"
                }
              },
              "required": ["template"]
            }
          }
        },
        "required": ["files", "location", "name"]
      }
    },
    "project_template": {
      "description": "The project template options",
      "type": "object",
      "properties": {
        "configuration_filename": {
          "description": "Name of the project configuration JSON file [optional]",
          "default": "jupyter-project.json",
          "type": "string"
        },
        "configuration_schema": {
          "description": "JSON schema describing the project configuration file [optional]",
          "default": {
            "type": "object",
            "properties": {"name": {"type": "string"}},
            "required": ["name"],
          },
          "type": "object"
        },
        "conda_pkgs": {
          "default": null,
          "description": "Type of conda environment or space separated list of conda packages (requires `jupyter_conda`) [optional]",
          "type": "string"
        },
        "default_path": {
          "description": "Default file or folder to open; relative to the project root [optional]",
          "type": "string"
        },
        "editable_install": {
          "description": "Should the project be installed in pip editable mode in the conda environment?",
          "type": "boolean",
          "default": true
        },
        "filter_kernel": {
          "description": "Should the kernel be filtered to match only the conda environment?",
          "type": "boolean",
          "default": true
        },
        "folder_name": {
          "description": "Project name (support Jinja2 templating using the schema parameters) [optional]",
          "default": "{{ name|lower|replace(' ', '_') }}",
          "type": "string"
        },
        "module": {
          "description": "Python package containing the template [optional]",
          "type": "string"
        },
        "schema": {
          "description": "JSON schema describing the template parameters [optional]",
          "default": {
            "type": "object",
            "properties": {"name": {"type": "string", "pattern": "^[a-zA-Z_]\\w*$"}},
            "required": ["name"],
          },
          "type": "object"
        },
        "template": {
          "description": "Cookiecutter template source",
          "default": null,
          "type": "string"
        }
      },
      "required": ["template"]
    }
  }
}
```

## Troubleshoot

If you are seeing the frontend extension but it is not working, check
that the server extension is enabled:

```bash
jupyter serverextension list
```

If the server extension is installed and enabled but you are not seeing
the frontend, check the frontend is installed:

```bash
jupyter labextension list
```

If it is installed, try:

```bash
jupyter lab clean
jupyter lab build
```

## Contributing

The frontend extension is based on [uniforms](https://uniforms.tools/) with its
[material-ui](https://material-ui.com/) flavor to handle and display automatic
forms from JSON schema.

### Install

The `jlpm` command is JupyterLab's pinned version of
[yarn](https://yarnpkg.com/) that is installed with JupyterLab. You may use
`yarn` or `npm` in lieu of `jlpm` below.

```bash
# Clone the repo to your local environment
# Move to jupyter-project directory

# Install server extension
pip install -e .[test]
# Register server extension
jupyter serverextension enable --py jupyter_project

# Install dependencies
jlpm
# Build Typescript source
jlpm build
# Link your development version of the extension with JupyterLab
jupyter labextension link .
# Rebuild Typescript source after making changes
jlpm build
# Rebuild JupyterLab after making any changes
jupyter lab build
```

You can watch the source directory and run JupyterLab in watch mode to watch for changes in the extension's source and automatically rebuild the extension and application.

```bash
# Watch the source directory in another terminal tab
jlpm watch
# Run jupyterlab in watch mode in one terminal tab
jupyter lab --watch
```

> To run with an working example, execute `jupyter lab` from the binder folder to use the local `jupyter_notebook_config.json` as configuration.

## Uninstall

With pip:

```bash
pip uninstall jupyter-project
jupyter labextension uninstall jupyter-project
```

Or with pip:

```bash
conda remove jupyter-project
jupyter labextension uninstall jupyter-project
```

## Alternatives

Don't like what you see here? Try these other approaches:

- [jupyterlab-starters](https://github.com/deathbeds/jupyterlab-starters)
- [jupyterlab_templates](https://github.com/timkpaine/jupyterlab_templates)
