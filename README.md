# jupyter-project

![Github Actions Status](https://github.com/fcollonval/jupyter-project/workflows/Build/badge.svg)

An JupyterLab extension to handle project folders. It adds the ability to 
generate project from a [cookiecutter](https://cookiecutter.readthedocs.io/en/latest/) template as well as generate files
from [Jinja2](https://jinja.palletsprojects.com/en/master/) templates. Those templates can be parametrized directly from
the frontend by specifying a [JSON schema](https://json-schema.org/).


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

### Uninstall

```bash
pip uninstall jupyter_project

jupyter labextension uninstall jupyter-project
```
