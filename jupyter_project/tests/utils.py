import json
from typing import List

from traitlets.config import Config

# Shim for notebook server or jupyter_server
#
# Provides:
#  - ServerTestBase
#  - assert_http_error
#  - url_path_join

try:
    from notebook.tests.launchnotebook import (
        assert_http_error,
        NotebookTestBase as ServerTestBase,
    )
    from notebook.utils import url_path_join
except ImportError:
    from jupyter_server.tests.launchnotebook import assert_http_error  # noqa
    from jupyter_server.tests.launchserver import ServerTestBase  # noqa
    from jupyter_server.utils import url_path_join  # noqa

from jupyter_project.handlers import NAMESPACE


class APITester(object):
    """Wrapper for REST API requests"""

    url = f"/{NAMESPACE}"

    def __init__(self, request):
        self.request = request

    def _req(self, verb: str, path: List[str], body=None, params=None):
        if body is not None:
            body = json.dumps(body)
        response = self.request(
            verb, url_path_join(self.url, *path), data=body, params=params
        )

        if 400 <= response.status_code < 600:
            try:
                response.reason = response.json()["message"]
            except Exception:
                pass
        response.raise_for_status()

        return response

    def delete(self, path: List[str], body=None, params=None):
        return self._req("DELETE", path, body, params)

    def get(self, path: List[str], body=None, params=None):
        return self._req("GET", path, body, params)

    def patch(self, path: List[str], body=None, params=None):
        return self._req("PATCH", path, body, params)

    def post(self, path: List[str], body=None, params=None):
        return self._req("POST", path, body, params)


class ServerTest(ServerTestBase):

    # Force extension enabling - Disabled by parent class otherwise
    config = Config({"NotebookApp": {"nbserver_extensions": {"jupyter_project": True}}})

    def setUp(self):
        super(ServerTest, self).setUp()
        self.api_tester = APITester(self.request)
