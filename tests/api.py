import json
import os
import pathlib
import unittest

from chillapi.api import ChillApi
from chillapi.app.config import ChillApiModuleLoader, TableExtensions, ApiConfig
from chillapi.app.file_utils import read_yaml
from chillapi.exceptions.api_manager import TableNotExist, ColumnNotExist

CWD = pathlib.Path(__file__).parent.absolute()


# class ChillApiTestConfig(unittest.TestCase):
#     def testTableNotFoundError(self):
#         self.assertRaises(TableNotExist, ChillApi, None, f'{CWD}/fixtures/api_table_no_exists.yaml', f'{CWD}/outputs')

class ChillApiTestErrors(unittest.TestCase):
    def tearDown(self) -> None:
        ApiConfig._instances = {}

    def testTableNotFoundError(self):
        api_config = read_yaml(f'{CWD}/fixtures/api_table_no_exists.yaml')

        module_loader = ChillApiModuleLoader()
        table_extension = TableExtensions(module_loader)
        # config = ApiConfig(**{**api_config, **{'table_extensions': table_extension}})

        self.assertRaises(TableNotExist, ApiConfig, **{**api_config, **{'table_extensions': table_extension}})

    # def testTableColumnNotFoundInExtensionError(self):
    #     api_config = read_yaml(f'{CWD}/fixtures/api_table_no_exists.yaml')
    #
    #     module_loader = ChillApiModuleLoader()
    #     table_extension = TableExtensions(module_loader)
    #     # config = ApiConfig(**{**api_config, **{'table_extensions': table_extension}})
    #
    #     self.assertRaises(ColumnNotExist, ApiConfig, **{**api_config, **{'table_extensions': table_extension}})
    #
    #     # self.assertRaises(ColumnNotExist, ChillApi, None, f'{CWD}/fixtures/api_table_extension_column_no_exists.yaml', f'{CWD}/outputs')
