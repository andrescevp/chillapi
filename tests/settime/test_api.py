import os
import pathlib
import unittest

from unittest import mock

from chillapi.abc import TableExtension
from chillapi.api import ChillApi
from chillapi.app.config import (
    ApiConfig, ChillApiExtensions,
    ChillApiModuleLoader,
    )
from chillapi.app.file_utils import read_yaml
from chillapi.exceptions.api_manager import ColumnNotExist, TableNotExist
from chillapi.extensions.events import NullAfterResponseEvent
from my_app.default_events import MyAfterResponseEvent

CWD = pathlib.Path(__file__).parent.absolute()


class ChillApiTestErrors(unittest.TestCase):
    def tearDown(self) -> None:
        ApiConfig.reset()


    def testTableNotFoundError(self):
        api_config = read_yaml(f'{CWD}/../fixtures/api_table_no_exists.yaml')

        module_loader = ChillApiModuleLoader()
        table_extension = ChillApiExtensions(module_loader)
        self.assertRaises(
                TableNotExist,
                ApiConfig,
                **{**api_config, **{'extensions': table_extension}}
                )


    def testTableColumnNotFoundInExtensionError(self):
        api_config = read_yaml(
                f'{CWD}/../fixtures/api_table_extension_column_no_exists.yaml'
                )

        module_loader = ChillApiModuleLoader()
        table_extension = ChillApiExtensions(module_loader)

        self.assertRaises(
                ColumnNotExist,
                ApiConfig,
                **{**api_config, **{'extensions': table_extension}}
                )


    def testModules(self):
        # api_config = read_yaml(
        #         f'{CWD}/../fixtures/api.yaml'
        #         )
        #
        # module_loader = ChillApiModuleLoader()
        # table_extension = ChillApiExtensions(module_loader)

        _resources = ChillApi(config_file = f'{CWD}/../fixtures/api.yaml')

        self.assertTrue(_resources.module_loader.has_module('my_app.audit'))
        self.assertTrue(_resources.module_loader.has_module('my_app.default_events'))
        self.assertTrue(_resources.module_loader.has_module('my_app.auth'))
        self.assertTrue(_resources.module_loader.has_module('wtforms.validators'))

        self.assertTrue(isinstance(_resources.table_extensions.tables['BookCategory']['soft_delete'], TableExtension))
        self.assertTrue(_resources.table_extensions.tables['BookCategory']['soft_delete'].enabled)

        self.assertFalse(_resources.table_extensions.tables['Dummy']['soft_delete'].enabled)

        self.assertFalse(isinstance(_resources.table_extensions.tables['DummyCreate']['soft_delete'], NullAfterResponseEvent))
        self.assertTrue(_resources.table_extensions.tables['DummyCreate']['on_create_timestamp'].enabled)
        self.assertTrue(_resources.table_extensions.tables['DummyCreate']['on_create_timestamp'].config['default_field'] == 'creation')

        self.assertTrue(isinstance(_resources.table_extensions.tables['Author']['after_response'], MyAfterResponseEvent))
