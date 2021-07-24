import copy
import importlib
import os
from typing import Dict, List

import slug
from mergedeep import merge as dict_deepmerge
from sqlalchemy.engine import Inspector
from sqlalchemy.orm.scoping import ScopedSession

from ..abc import Repository, TableExtension
from ..app import (
    _app_defaults,
    _database_defaults,
    _environment_defaults,
    _logger_defaults,
    _sql_default_config,
    _sql_template_default_config,
    _table_default_config,
    _tables_default_config,
)
from ..database.connection import create_db_toolbox, TYPE_RELATIONAL
from ..database.repository import DataRepository
from ..exceptions.api_manager import ColumnNotExist, ConfigError, TableNotExist
from ..extensions import LIVECYCLE_EXTENSIONS, REQUEST_EXTENSIONS
from ..extensions.record_livecycle import INTERNAL_EXTENSION_DEFAULTS
from ..logger.app_loggers import set_logger_config

CWD = os.getcwd()


class ChillApiModuleLoader(dict):
    """Module loader class"""

    _modules: dict = {}
    loaded = False

    def add_module(self, module: str):
        """
        Add a imported instance of the specified python package
        :param module: str:

        """
        if self.has_module(module):
            return

        self._modules[module] = importlib.import_module(module)

    def get_module(self, module: str):
        """

        :param module: str:

        """
        if not self.has_module(module):
            raise ConfigError(f"{module} not loaded!")

        return self._modules.get(module)

    def get_module_attr(self, module: str, attr: str, args: dict):
        """

        :param module: str:
        :param attr: str:
        :param args: dict:

        """
        return getattr(self.get_module(module), attr)(**args)

    def has_module_attr(self, module: str, attr: str):
        """

        :param module: str:
        :param attr: str:

        """
        return hasattr(self.get_module(module), attr)

    def has_module(self, module: str):
        """

        :param module: str:

        """
        return module in self._modules.keys()


class ChillApiExtensions(dict):
    """Module wrapper to load modules as extensions in the different library contexts"""

    tables: dict = dict({})
    app: dict = dict({})

    def __init__(self, module_loader: ChillApiModuleLoader):
        super().__init__()
        self.module_loader = module_loader
        self.internal_extension_map = INTERNAL_EXTENSION_DEFAULTS.copy()

    def set_extension(self, name: str, package_config: dict, type: str = "app"):
        """

        :param name: str:
        :param package_config: dict:
        :param type: str:  (Default value = "app")

        """
        self.module_loader.add_module(package_config["package"])

        extension = self.module_loader.get_module_attr(
            package_config["package"],
            package_config["handler"],
            package_config["handler_args"] if "handler_args" in package_config else {},
        )

        _attr = getattr(self, type)
        _attr[name] = extension
        setattr(self, type, _attr)

    def set_livecycle_table_extension(
        self,
        extension_name: str,
        columns: dict,
        extension_config: dict,
        table_name: str,
        repository: Repository,
        inspector: Inspector,
        source_key: str,
    ):
        """

        :param extension_name: str:
        :param columns: dict:
        :param extension_config: dict:
        :param table_name: str:
        :param repository: Repository:
        :param inspector: Inspector:

        """
        _extension = self.internal_extension_map["livecycle"][extension_name]
        extension = _extension(
            **{"config": extension_config, "table": table_name, "repository": repository, "columns": columns, "inspector": inspector}
        )
        extension.validate()

        if source_key not in self.tables.keys():
            self.tables[source_key] = {}
        if table_name not in self.tables[source_key].keys():
            self.tables[source_key][table_name] = {}
        self.tables[source_key][table_name][extension_name] = extension

    def set_request_table_extension(self, extension_name: str, extension_config: dict, table_name: str, source_key: str):
        """

        :param extension_name: str:
        :param extension_config: dict:
        :param table_name: str:

        """
        self.module_loader.add_module(extension_config["package"])

        extension = self.module_loader.get_module_attr(
            extension_config["package"],
            extension_config["handler"],
            extension_config["handler_args"],
        )

        if source_key not in self.tables.keys():
            self.tables[source_key] = {}

        if table_name not in self.tables[source_key].keys():
            self.tables[source_key][table_name] = {}
        self.tables[source_key][table_name][extension_name] = extension

    def set_validator_column_table_extension(self, column_name: str, extension_config: dict, table_name: str, source_key: str):
        """

        :param column_name: str:
        :param extension_config: dict:
        :param table_name: str:

        """
        self.module_loader.add_module(extension_config["package"])

        extension = self.module_loader.get_module_attr(
            extension_config["package"],
            extension_config["handler"],
            extension_config["handler_args"],
        )

        if source_key not in self.tables.keys():
            self.tables[source_key] = {}
        if table_name not in self.tables[source_key].keys():
            self.tables[source_key][table_name] = {}
        if "validators" not in self.tables[source_key][table_name].keys():
            self.tables[source_key][table_name]["validators"] = {}
        if column_name not in self.tables[source_key][table_name]["validators"].keys():
            self.tables[source_key][table_name]["validators"][column_name] = []
        self.tables[source_key][table_name]["validators"][column_name].append(extension)

    def is_extension_enabled(self, extension_name: str, type: str = "app") -> bool:
        """

        :param extension_name: str:
        :param type: str:  (Default value = "app")

        """
        return hasattr(getattr(self, type), extension_name)

    def is_table_extension_enabled(self, source_key: str, table_name: str, extension_name: str) -> bool:
        """

        :param table_name: str:
        :param extension_name: str:

        """
        if not hasattr(self.tables, source_key):
            return False

        if not hasattr(self.tables[source_key], table_name):
            return False

        return hasattr(getattr(self.tables[source_key], table_name), extension_name)

    def get_extension(self, extension_name: str, type: str = "app"):
        """

        :param extension_name: str:
        :param type: str:  (Default value = "app")

        """
        return getattr(self, type)[extension_name]

    def get_table_extension(self, source_key: str, table_name: str, extension_name: str) -> TableExtension:
        """

        :param table_name: str:
        :param extension_name: str:

        """
        return getattr(getattr(self.tables[source_key], table_name), extension_name)


class ApiConfig:
    """ """

    app: dict = {}
    environment: dict = {}
    logger: dict = {}
    database: dict = {}
    model_names: List = []
    repository: Dict[str, Repository] = {}
    db: Dict[str, ScopedSession] = {}
    db_inspector: Dict[str, Inspector] = {}

    def __init__(self, extensions: ChillApiExtensions, app: dict, environment: dict = None, logger: dict = None, database: dict = None):
        self.extensions = extensions
        app = {} if app is None else app
        environment = {} if environment is None else environment
        logger = {} if logger is None else logger
        database = {} if database is None else database

        self.logger = dict(dict_deepmerge({}, _logger_defaults, logger))

        set_logger_config(self.logger)

        self.app = dict(dict_deepmerge({}, _app_defaults, app))

        self.environment = dict(dict_deepmerge({}, _environment_defaults, environment))

        # if "__CHILLAPI_DB_DSN__" in self.environment and self.environment["__CHILLAPI_DB_DSN__"].startswith("$"):
        #     self.environment["__CHILLAPI_DB_DSN__"] = os.getenv(self.environment["__CHILLAPI_DB_DSN__"].replace("$", "", 1))

        for _env_key in self.environment.keys():
            os.environ.setdefault(_env_key, self.environment[_env_key])

        for source_key in database.keys():
            self.database[source_key] = dict(dict_deepmerge({}, _database_defaults, database[source_key]))
            if "defaults" in self.database[source_key] and "tables" in self.database[source_key]["defaults"]:
                self.database[source_key]["defaults"]["tables"] = dict(
                    dict_deepmerge({}, _tables_default_config, self.database[source_key]["defaults"]["tables"])
                )
            else:
                self.database[source_key]["defaults"]["tables"] = _tables_default_config

            self._init_tables(source_key)

            if "sql" in self.database[source_key] and len(self.database[source_key]["sql"]) > 0:
                self.database[source_key]["sql"] = [dict(dict_deepmerge({}, _sql_default_config, t)) for t in self.database[source_key]["sql"]]

            if "templates" in self.database and len(self.database["templates"]) > 0:
                self.database[source_key]["templates"] = [
                    dict(dict_deepmerge({}, _sql_template_default_config, t)) for t in self.database[source_key]["templates"]
                ]

            db_tools = create_db_toolbox(self.database[source_key])

            self.db[source_key] = db_tools["session"]
            self.db_inspector[source_key] = db_tools["inspector"]
            type = db_tools["type"]

            self.repository[source_key] = DataRepository(self.db[source_key])

            if type == TYPE_RELATIONAL:
                _db_tables = self.db_inspector[source_key].get_table_names()
                for key, _table in enumerate(self.database[source_key]["tables"]):
                    _table_name = _table["name"]
                    if _table_name not in _db_tables:
                        raise TableNotExist(f"Table {_table_name} do not exist!")

                self.load_table_columns(source_key)
                self.load_extensions(source_key)

    def _init_tables(self, source_key):
        """ """
        if "tables" in self.database[source_key] and len(self.database[source_key]["tables"]) > 0:
            _global_defaults = copy.deepcopy(self.database[source_key]["defaults"]["tables"])
            if "audit_logger" in _global_defaults["extensions"]:
                del _global_defaults["extensions"]["audit_logger"]

            self.database[source_key]["tables"] = [
                dict(
                    dict_deepmerge(
                        {},
                        dict_deepmerge(
                            {},
                            _table_default_config,
                            _global_defaults,
                        ),
                        t,
                    )
                )
                for t in self.database[source_key]["tables"]
            ]
            for key, _table in enumerate(self.database[source_key]["tables"]):
                print(_table)
                if "fields_excluded" in _table:
                    for _method in _table["fields_excluded"].keys():
                        if _method == "all":
                            continue
                        for _endpoint in _table["fields_excluded"][_method].keys():
                            if _table["fields_excluded"][_method][_endpoint]:
                                _table["fields_excluded"][_method][_endpoint].extend(
                                    x for x in _table["fields_excluded"]["all"] if x not in _table["fields_excluded"][_method][_endpoint]
                                )
                            else:
                                _table["fields_excluded"][_method][_endpoint] = _table["fields_excluded"]["all"]

                _model_name = self.get_class_name_from_model_name(_table["name"] if not _table["alias"] else _table["alias"])
                _table["model_name"] = _model_name
                _table["slug"] = slug.slug(_table["name"] if not _table["alias"] else _table["alias"])
                if _model_name in self.model_names:
                    raise ConfigError(
                        f"""
                        Table '{_table['name']}' with alias '{_table['alias']}' is already defined.
                        Please add or change the alias
                        """
                    )
                self.model_names.append(_model_name)

    @classmethod
    def reset(cls):
        """ """
        cls.app = {}
        cls.environment = {}
        cls.logger = {}
        cls.database = {}
        cls.model_names = []

    def get_columns_table_details(self, table_name, source_key):
        """

        :param table_name:

        """
        return self.db_inspector[source_key].get_columns(table_name)

    def get_class_name_from_model_name(self, model_name):
        """

        :param model_name:

        """
        class_name = model_name.replace("_", " ").title().replace(" ", "")
        return class_name

    def validate_sources(self):
        """ """
        pass

    def get_table_columns(self, name, source_key):
        """

        :param name:

        """
        table_columns = self.get_columns_table_details(name, source_key)
        return {v["name"]: v for i, v in enumerate(table_columns)}

    def load_table_columns(self, source_key):
        """ """
        for _it, table in enumerate(self.database[source_key]["tables"]):
            table_name = table["name"]
            _table_columns = self.get_table_columns(table_name, source_key)
            self.database[source_key]["tables"][_it]["columns"] = _table_columns

    def load_extension(self, table_config: dict, extension_name: str, source_key: str):
        """

        :param table_config: dict:
        :param extension_name: str:

        """
        table_name = table_config["model_name"]
        if extension_name in LIVECYCLE_EXTENSIONS and self.extensions.is_table_extension_enabled(table_name, extension_name, source_key) is False:
            self.extensions.set_livecycle_table_extension(
                extension_name,
                table_config["columns"],
                table_config["extensions"][extension_name],
                table_name,
                self.repository[source_key],
                self.db_inspector[source_key],
                source_key,
            )

        if extension_name in REQUEST_EXTENSIONS and self.extensions.is_table_extension_enabled(table_name, extension_name, source_key) is False:
            _extension_conf = table_config["extensions"][extension_name]
            self.extensions.set_request_table_extension(extension_name, _extension_conf, table_name, source_key)

        if extension_name == "validators":
            _columns_in_table = table_config["columns"].keys()
            for column_to_validate, validators in table_config["extensions"][extension_name].items():
                if column_to_validate not in _columns_in_table:
                    raise ColumnNotExist(f"{column_to_validate} to validate does not exists!")
                for _v, validator in enumerate(validators):
                    self.extensions.set_validator_column_table_extension(column_to_validate, validator, table_name, source_key)
            # _extension_conf = table_config["extensions"][extension_name]
            # self.extensions.set_request_table_extension(extension_name, _extension_conf, table_name)

    def load_extensions(self, source_key):
        """ """
        # if not self.extensions.is_extension_enabled("audit"):
        #     self.extensions.set_extension("audit", self.database[source_key]["defaults"]["tables"]["extensions"]["audit_logger"])

        for _it, table in enumerate(self.database[source_key]["tables"]):
            for _extension_name in table["extensions"].keys():
                self.load_extension(table, _extension_name, source_key)

    def to_dict(self):
        """ """
        return {
            "app": self.app,
            "logger": self.logger,
            "environment": self.environment,
            "database": self.database,
        }
