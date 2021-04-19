import unittest

from chillapi.app.config import ChillApiModuleLoader


class ChillApiModuleLoaderTest(unittest.TestCase):
    def testModuleNotFoundError(self):
        loader = ChillApiModuleLoader()
        self.assertRaises(ModuleNotFoundError, loader.add_module, 'do.not.exits')

    def testModuleAttachment(self):
        loader = ChillApiModuleLoader()
        loader.add_module('my_app.audit')
        self.assertTrue(loader.has_module('my_app.audit'))

