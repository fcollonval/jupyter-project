import json
from pathlib import Path

from jupyter_packaging import get_version
from packaging.version import parse


def assert_equal_version():
    cdir = Path(__file__).parent
    server_version = parse(get_version(str(cdir / "jupyter_project" / "_version.py")))
    package_json = cdir / "package.json"
    package_config = json.loads(package_json.read_text())
    jlab_version = parse(package_config.get("version", "0"))
    assert server_version == jlab_version, f"Frontend ({jlab_version}) and server ({server_version}) versions are not matching."
