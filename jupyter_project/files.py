"""
 Simple regex validation for an SVG string taken from:
 https://github.com/sindresorhus/is-svg
 
 MIT License
 
 Copyright (c) Sindre Sorhus <sindresorhus@gmail.com> (sindresorhus.com)
 
 Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:
 
 The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.
 
 THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
"""
import pathlib
import re
from typing import Dict

from traitlets import HasTraits, List, TraitError, Unicode, validate
from traitlets.utils.bunch import Bunch

from .autoinstance import AutoInstance
from .traits import JSONSchema, Path


SVG_PATTERN = re.compile(
    r"^\s*(?:<\?xml[^>]*>\s*)?(?:<!doctype svg[^>]*\s*(?:\[?(?:\s*<![^>]*>\s*)*\]?)*[^>]*>\s*)?(?:<svg[^>]*>.*<\/svg>|<svg[^/>]*\/\s*>)\s*$",
    re.IGNORECASE | re.DOTALL,
)


class FileTemplate(HasTraits):
    """Jinja2 file template class."""

    default_name = Unicode(
        default_value="Untitled",
        help="Default file name (without extension; support Jinja2 templating using the schema parameters)",
        config=True,
    )
    destination = Path(help="Relative destination folder [optional]", config=True)
    icon = Unicode(
        default_value=None,
        allow_none=True,
        help="Template icon to display in the frontend [optional]",
        config=True,
    )
    schema = JSONSchema(
        help="JSON schema list describing the templates parameters [optional]", config=True
    )
    template = Path(help="Template path", config=True)
    template_name = Unicode(help="Template name in the UI [optional]", config=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Force checking the default value as they are not valid
        self._valid_template({"value": self.template})

    def __eq__(self, other: "FileTemplate") -> bool:
        if self is other:
            return True

        for attr in ("default_name", "destination", "schema", "template"):
            if getattr(self, attr) != getattr(other, attr):
                return False
        return True

    @validate("default_name")
    def _valid_default_name(self, proposal: Bunch) -> str:
        if len(proposal["value"]) == 0:
            raise TraitError("'default_name' cannot be empty.")
        return proposal["value"]

    @validate("icon")
    def _valid_icon(self, proposal: Bunch) -> str:
        if proposal["value"] is not None:
            if SVG_PATTERN.match(proposal["value"]) is None:
                raise TraitError("'icon' is not a valid SVG.")
        return proposal["value"]

    @validate("template")
    def _valid_template(self, proposal: Bunch) -> str:
        if proposal["value"] == pathlib.Path(""):
            raise TraitError("'template' cannot be empty.")
        return proposal["value"]


class FileTemplateLoader(HasTraits):
    """Jinja2 template file location class."""

    files = List(
        trait=AutoInstance(FileTemplate),
        minlen=1,
        help="List of template files",
        config=True,
    )
    location = Unicode(help="Templates path", config=True)
    module = Unicode(
        help="Python package containing the templates 'location' [optional]",
        config=True,
    )
    name = Unicode(help="Templates group name", config=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Force checking the default value as they are not valid
        self._valid_name({"value": self.name})
        self._valid_location({"value": self.location})
        if len(self.files) == 0:
            raise TraitError("'files' cannot be empty.")

    def __eq__(self, other: "FileTemplateLoader") -> bool:
        for attr in ("files", "location", "module", "name"):
            if getattr(self, attr) != getattr(other, attr):
                return False
        return True

    @validate("name")
    def _valid_name(self, proposal: Bunch) -> str:
        if len(proposal["value"]) == 0:
            raise TraitError("'name' cannot be empty.")
        return proposal["value"]

    @validate("location")
    def _valid_location(self, proposal: Bunch) -> str:
        if len(proposal["value"]) == 0:
            raise TraitError("'location' cannot be empty.")
        return proposal["value"]
