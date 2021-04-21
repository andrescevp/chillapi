import pathlib
import unittest

from chillapi.app.config import ApiConfig, ChillapiExtensions, \
    ChillApiModuleLoader
from chillapi.app.file_utils import read_yaml
from chillapi.exceptions.api_manager import ColumnNotExist, TableNotExist

CWD = pathlib.Path(__file__).parent.absolute()


class ChillApiTestErrors(unittest.TestCase):
    def tearDown(self) -> None:
        ApiConfig.reset()

    def testTableNotFoundError(self):
        api_config = read_yaml(f'{CWD}/fixtures/api_table_no_exists.yaml')

        module_loader = ChillApiModuleLoader()
        table_extension = ChillapiExtensions(module_loader)
        self.assertRaises(
                TableNotExist,
                ApiConfig,
                **{**api_config, **{'table_extensions': table_extension}}
                )

    def testTableColumnNotFoundInExtensionError(self):
        api_config = read_yaml(
                f'{CWD}/fixtures/api_table_extension_column_no_exists.yaml'
                )

        module_loader = ChillApiModuleLoader()
        table_extension = ChillapiExtensions(module_loader)

        self.assertRaises(
                ColumnNotExist,
                ApiConfig,
                **{**api_config, **{'table_extensions': table_extension}}
                )
