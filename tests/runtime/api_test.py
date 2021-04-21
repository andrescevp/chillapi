import json
import unittest

from chillapi.app.config import ChillApiModuleLoader
from tests.runtime import appurl, DBCase, header


class ReadTest(DBCase):
    def test_list_disallowed(self):
        rv = self.app.get(appurl % "swagger.json", headers=header)
        response = json.loads(rv.data)
        #veritas = '{\n  "objects": [], \n  "total_pages": 0, \n  "page": 1\n}'
        veritas = "401"
        self.assertTrue('/create/author' in response['paths'].keys())
