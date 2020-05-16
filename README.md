# jupyter-project

[![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/fcollonval/jupyter-project/master?urlpath=lab)
[![Github Actions Status](https://github.com/fcollonval/jupyter-project/workflows/Test/badge.svg)](https://github.com/fcollonval/jupyter-project/actions?query=workflow%3ATest)
[![Coverage Status](https://coveralls.io/repos/github/fcollonval/jupyter-project/badge.svg?branch=master)](https://coveralls.io/github/fcollonval/jupyter-project?branch=master)


An JupyterLab extension to handle (a unique) project and files templates. It adds the ability
to generate projects from a [cookiecutter](https://cookiecutter.readthedocs.io/en/latest/) template as well as generate files
from [Jinja2](https://jinja.palletsprojects.com/en/master/) templates. Those templates can be parametrized directly from
the frontend by specifying [JSON schemas](https://json-schema.org/).


This extension is composed of a Python package named `jupyter_project`
for the server extension and a NPM package named `jupyter-project`
for the frontend extension.


## Requirements

* JupyterLab = 1.x
* cookiecutter
* jinja2
* jsonschema

## Install

Note: You will need NodeJS to install the extension.

```bash
pip install jupyter_project
jupyter lab build
```

### Configuring the extension

By default, this extension will not add anything to JupyterLab as the templates must be configured
as part of the server extension configuration key **JupyterProject** (see [Jupyter server configuration](https://jupyter-notebook.readthedocs.io/en/stable/config_overview.html#) for more information).

The configuration example for Binder will be described next - this is the file [binder/jupyter_notebook_config.json](binder/jupyter_notebook_config.json).

The section for this extension must be named **JupyterProject**:

```json5
// ./binder/jupyter_notebook_config.json#L7-L7

"JupyterProject": {
```

It accepts to optional keys: *file_templates* and *project_template*. The first defines a list
of places containing templated files. And the second describe the project template. They can
both exist alone (i.e. only file templates or only the project template).

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

The last parameter appearing here is *name*. It described uniquely the source of file templates.

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

* `template_name`: A nicer name for the template to be displayed in the frontend.
* `default_name`: Default name for the file generated from the template (the string may contain Jinja2 variables defined in the `schema`).
* `destination`: If you are using the project template, the generated file will be placed
within the destination folder inside the active project folder. If no project is active
the file will be written in the current folder.


The latest file template example is a complete example of all possibilities (including 
type of variables that you could used in the schema):

```json5
// ./binder/jupyter_notebook_config.json#L17-L73

{
  "destination": "notebooks",
  "icon": "<svg xmlns=\"http://www.w3.org/2000/svg\" viewBox=\"0 0 16 16\"> <path d=\"M 0.62754418,5.7679165 V 13.566266 L 8.5124129,13.135686 V 6.6832665 Z\" style=\"fill:#353564;fill-opacity:1;fill-rule:evenodd;stroke:none;stroke-width:2;stroke-linejoin:round;stroke-miterlimit:4;stroke-dasharray:none;stroke-opacity:1\" /> <path d=\"m 0.62754418,13.566266 2.80479342,1.46719 12.1283534,-1.12061 -7.0482781,-0.77716 z\" style=\"fill:#afafde;fill-opacity:1;fill-rule:evenodd;stroke:none;stroke-width:2;stroke-linejoin:round;stroke-miterlimit:4;stroke-dasharray:none;stroke-opacity:1\" /> <path d=\"M 8.5124129,6.6832665 15.560691,3.3386664 V 13.912846 l -7.0482781,-0.77716 z\" style=\"fill:#e9e9ff;fill-opacity:1;fill-rule:evenodd;stroke:none;stroke-width:2;stroke-linejoin:round;stroke-miterlimit:4;stroke-dasharray:none;stroke-opacity:1\" /> <path d=\"M 0.62754418,5.7679165 3.4323376,0.28889643 15.560691,3.3386664 8.5124129,6.6832665 Z\" style=\"fill:#4d4d9f;fill-opacity:1;fill-rule:evenodd;stroke:none;stroke-width:2;stroke-linejoin:round;stroke-miterlimit:4;stroke-dasharray:none;stroke-opacity:1\" /> <path d=\"M 3.4323376,0.28889643 V 15.033456 L 15.560691,13.912846 V 3.3386664 Z\" style=\"fill:#d7d7ff;fill-opacity:1;fill-rule:evenodd;stroke:none;stroke-width:2;stroke-linejoin:round;stroke-miterlimit:4;stroke-dasharray:none;stroke-opacity:1\" /> <path d=\"M 0.62754418,5.7679165 3.4323376,0.28889643 V 15.033456 l -2.80479342,-1.46719 z\" style=\"fill:#8686bf;fill-opacity:1;fill-rule:evenodd;stroke:none;stroke-width:2;stroke-linejoin:round;stroke-miterlimit:4;stroke-dasharray:none;stroke-opacity:1\" /> <path class=\"jp-icon-accent0\" fill=\"#faff00\" d=\"m 12.098275,4.7065364 -4.9999997,-0.62651 v 8.9554396 l 4.9999997,-0.32893 v -1.1 l -3.4999997,0.19305 V 8.9065364 h 1.9999997 v -1.1 l -1.9999997,-0.1 V 5.3539365 l 3.4999997,0.3526 z\" style=\"fill-opacity:1;stroke:none;stroke-width:1px;stroke-linecap:butt;stroke-linejoin:miter;stroke-opacity:1\" /> </svg> ",
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

The second major configuration section is `project_template`. Each template must
specified a value for `template` that points to a valid [cookiecutter](https://cookiecutter.readthedocs.io/en/latest/)
template source:


```json5
// ./binder/jupyter_notebook_config.json#L96-L97

"project_template": {
  "template": "https://github.com/fcollonval/cookiecutter-data-science",
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
been generated:

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

### Uninstall

```bash
pip uninstall jupyter_project

jupyter labextension uninstall jupyter-project
```

## Changelog

### v0.1.0

- Handle Jinja2 file templates
- Handle project cookiecutter template
