import importlib
import json
import os
from typing import List

from dotenv import load_dotenv
from pathlib import Path

from jsonschema import validate, ValidationError
from mergedeep import merge as dict_deepmerge
from schemainspect import get_inspector
from sqlbag import S

from chillapi import SingletonMeta
from chillapi.abc import TableExtension, Repository
from chillapi.app.file_utils import read_yaml
from chillapi.exceptions.api_manager import ConfigError
from chillapi.extensions.record_livecycle import INTERNAL_EXTENSION_DEFAULTS

env_path = Path(os.getcwd()) / ".env"
load_dotenv(dotenv_path=env_path)

CONFIG_FILE = 'api.yaml'
SCHEMA_CONFIG_FILE = 'api.schema.json'

_virtual_modules_map = {}
api_config = read_yaml(CONFIG_FILE)
api_schema = json.load(open(SCHEMA_CONFIG_FILE, 'r'))

try:
    validate(instance=api_config, schema=api_schema)
except ValidationError as e:
    raise ConfigError(e)

# parse_config(api_config)

_app_defaults = {
    'name': 'api',
    'version': '0.0',
    'swagger_url': '/swagger',
    'swagger_ui_url': '/doc',
    'host': '0.0.0.0',
    'port': 8000,
    'debug': True,
}

_environment_defaults = {
    'APP_DB_URL': None,
    'APP_SECRET_KEY': 'this-is-not-so-secret',
}

_logger_defaults = {
    'app': {
        'output': 'stdout',
        'level': 10,
    },
    'audit_logger': {
        'output': 'stdout',
        'level': 10,
    },
    'error_handler': {
        'output': 'stdout',
        'level': 10,
    },
    'sqlalchemy': {
        'output': 'stdout',
        'level': 10,
    },
}

_database_defaults = {
    'name': None,
    'schema': 'public',
    'defaults': {
        'tables': {
            'id_field': 'id',
            'fields_excluded': {
                'all': None,
                'GET': {
                    'SINGLE': None,
                    'LIST': None,
                },
                'PUT': {
                    'SINGLE': None,
                    'LIST': None,
                },
                'POST': {
                    'SINGLE': None,
                    'LIST': None,
                },
            },
            'api_endpoints': {
                'PUT': ['SINGLE', 'LIST'],
                'GET': ['SINGLE', 'LIST'],
                'POST': ['SINGLE', 'LIST'],
                'DELETE': ['SINGLE', 'LIST'],
            },
            'extensions': {
                'soft_delete': {
                    'enable': False
                },
                'on_update_timestamp': {
                    'enable': False
                },
                'on_create_timestamp': {
                    'enable': False
                },
            }
        }
    },
    'tables': [],
    'sql': [],
    'templates': [],
}

_tables_default_config = {
    'id_field': 'id',
    'fields_excluded': {
        'all': None
    },
    'GET': {
        'SINGLE': None,
        'LIST': None,
    },
    'POST': {
        'SINGLE': None,
        'LIST': None,
    },
    'PUT': {
        'SINGLE': None,
        'LIST': None,
    },
    'api_endpoints': {
        'PUT': ['SINGLE', 'LIST'],
        'GET': ['SINGLE', 'LIST'],
        'POST': ['SINGLE', 'LIST'],
        'DELETE': ['SINGLE', 'LIST'],
    },
    'extensions': {
        'audit_logger': {
            'package': 'chillapi.extensions.audit',
            'audit_log_handler': 'NullAuditHandler',
            'audit_log_handler_args': {},
        },
        'soft_delete': {
            'enable': False
        },
        'on_update_timestamp': {
            'enable': False
        },
        'on_create_timestamp': {
            'enable': False
        },
    }
}

_table_default_config = {**_tables_default_config, **{'alias': None}}

_sql_default_config = {
    'name': None,
    'method': 'GET',
    'url': None,
    'sql': None,
    'query_parameters': None,
    'response_schema': None,
    'request_schema': None
}

_sql_template_default_config = {
    'name': None,
    'method': 'GET',
    'url': None,
    'template': None,
    'query_parameters': None,
    'response_schema': None,
    'request_schema': None
}


def _get_db_url(api_config):
    db_url = os.getenv("APP_DB_URL")
    if 'environment' in api_config and 'APP_DB_URL' in api_config['environment']:
        db_url = api_config['environment']['APP_DB_URL']
        if db_url.startswith('$'):
            db_url = os.getenv(db_url.replace('$', '', 1))
    return db_url


def _get_secret_key(api_config):
    secret_key = os.getenv("APP_SECRET_KEY", 'super-secret-key')
    if 'environment' in api_config and 'APP_SECRET_KEY' in api_config['environment']:
        secret_key = api_config['environment']['APP_SECRET_KEY']
    return secret_key


class ChillApiModuleLoader(dict, metaclass=SingletonMeta):
    _modules: dict = {}
    loaded = False

    def add_module(self, module: str):
        if hasattr(self._modules, module):
            return

        self._modules[module] = importlib.import_module(module)

    def get_module(self, module: str):
        if module not in self._modules.keys():
            raise ConfigError(f'{module} not loaded!')

        return self._modules.get(module)

    def get_module_attr(self, module: str, attr: str, args: dict):
        return getattr(self.get_module(module), attr)(**args)

    def has_module_attr(self, module: str, attr: str):
        return hasattr(self.get_module(module), attr)

    def has_module(self, module: str):
        return module not in self._modules.keys()


class TableExtensions(dict, metaclass=SingletonMeta):
    tables: dict = dict({})
    app: dict = dict({})

    def __init__(self, module_loader: ChillApiModuleLoader):
        super().__init__()
        self.module_loader = module_loader
        self.internal_extension_map = INTERNAL_EXTENSION_DEFAULTS.copy()

    def set_extension(self, name: str, package_config: dict, type: str = 'app'):
        self.module_loader.add_module(package_config['package'])

        extension = self.module_loader.get_module_attr(
            package_config['package'],
            package_config['audit_log_handler'],
            package_config['audit_log_handler_args'] if 'audit_log_handler_args' in package_config else {},
        )

        _attr = getattr(self, type)
        _attr[name] = extension
        setattr(self, type, _attr)

    def set_livecycle_table_extension(self, extension_name: str, columns: dict, extension_config: dict, table_name: str,
                                      repository: Repository):
        _extension = self.internal_extension_map['livecycle'][extension_name]
        print(table_name, extension_config)
        extension = _extension(
            **{'config': extension_config, 'table': table_name, 'repository': repository, 'columns': columns})
        extension.validate()

        if not hasattr(self.tables, table_name):
            self.tables[table_name] = {}
        self.tables[table_name] = extension

    def is_extension_enabled(self, extension_name: str, type: str = 'app') -> bool:
        return hasattr(getattr(self, type), extension_name)

    def is_table_extension_enabled(self, table_name: str, extension_name: str) -> bool:
        if hasattr(self.tables, table_name):
            return hasattr(getattr(self.tables, table_name), extension_name)
        return False

    def get_extension(self, extension_name: str, type: str = 'app') -> TableExtension:
        return getattr(getattr(self, type), extension_name)


class ApiConfig(metaclass=SingletonMeta):
    app: dict = {}
    environment: dict = {}
    logger: dict = {}
    database: dict = {}
    model_names: List = []

    def __init__(self, table_extensions: TableExtensions, app: dict, environment: dict = None, logger: dict = None,
                 database: dict = None):
        self.extensions = table_extensions
        app = {} if app is None else app
        environment = {} if environment is None else environment
        logger = {} if logger is None else logger
        database = {} if database is None else database

        self.app = dict(dict_deepmerge(
            {},
            _app_defaults,
            app
        ))

        self.environment = dict(dict_deepmerge(
            {},
            _environment_defaults,
            environment
        ))

        if 'APP_DB_URL' in self.environment and self.environment['APP_DB_URL'].startswith('$'):
            self.environment['APP_DB_URL'] = os.getenv(self.environment['APP_DB_URL'].replace('$', '', 1))

        for _env_key in self.environment.keys():
            os.environ.setdefault(_env_key, self.environment.get(_env_key))

        with S(self.environment.get('APP_DB_URL')) as s:
            self.db_inspector = get_inspector(s)

        self.logger = dict(dict_deepmerge(
            {},
            _logger_defaults,
            logger
        ))

        self.database = dict(dict_deepmerge(
            {},
            _database_defaults,
            database
        ))

        if 'defaults' in self.database and 'tables' in self.database['defaults']:
            self.database['defaults']['tables'] = dict(dict_deepmerge(
                {},
                _tables_default_config,
                self.database['defaults']['tables']
            ))
        else:
            self.database['defaults']['tables'] = _tables_default_config

        if 'tables' in self.database and len(self.database['tables']) > 0:
            self.database['tables'] = [dict(dict_deepmerge(
                {},
                dict_deepmerge(
                    {},
                    _table_default_config,
                    self.database['defaults']['tables'],

                ),
                t
            )) for t in self.database['tables']]

            for key, _table in enumerate(self.database['tables']):
                _model_name = self.get_class_name_from_model_name(_table['name'])
                if _table['alias']:
                    _model_name = self.get_class_name_from_model_name(_table['alias'])
                self.database['tables'][key]['model_name'] = _model_name
                if _model_name in self.model_names:
                    raise ConfigError(
                        f"""
                        Table '{_table['name']}' with alias '{_table['alias']}' is already defined.
                        Please add or change the alias
                        """
                    )
                self.model_names.append(_model_name)

        if 'sql' in self.database and len(self.database['sql']) > 0:
            self.database['sql'] = [dict(dict_deepmerge(
                {},
                _sql_default_config,
                t
            )) for t in self.database['sql']]

        if 'templates' in self.database and len(self.database['templates']) > 0:
            self.database['templates'] = [dict(dict_deepmerge(
                {},
                _sql_template_default_config,
                t
            )) for t in self.database['templates']]

        self.load_table_columns()

    def get_columns_table_details(self, table_name):
        return self.db_inspector.tables[f'"{self.database.get("schema")}"."{table_name}"'].columns

    def get_class_name_from_model_name(self, model_name):
        class_name = model_name.replace("_", " ").title().replace(" ", "")
        return class_name

    def validate_sources(self):
        pass

    def get_table_columns(self, name):
        table_columns = self.get_columns_table_details(name)
        return {name: v for name, v in table_columns.items()}

    def load_table_columns(self):
        for _it, table in enumerate(self.database['tables']):
            table_name = table['name']
            _table_columns = self.get_table_columns(table_name)
            self.database['tables'][_it]['columns'] = _table_columns

    def load_extension(self, repository: Repository, table_config: dict, extension_name : str):
        table_name = table_config['name']
        if not self.extensions.is_table_extension_enabled(table_name, extension_name):
            self.extensions.set_livecycle_table_extension(
                extension_name,
                table_config['columns'],
                table_config['extensions'][extension_name],
                table_name,
                repository
            )

    def load_extensions(self, repository: Repository):
        if not self.extensions.is_extension_enabled('audit'):
            self.extensions.set_extension('audit', self.database['defaults']['tables']['extensions']['audit_logger'])

        for table in self.database['tables']:
            for _extension_name in table['extensions'].keys():
                if _extension_name == 'audit_logger':
                    continue
                self.load_extension(repository, table, _extension_name)

        # set_logger_config(self.logger, _custom_audit_logger_setup)


module_loader = ChillApiModuleLoader()
table_extension = TableExtensions(module_loader)
config = ApiConfig(**{**api_config, **{'table_extensions': table_extension}})

# print(config.database['tables'][1])
# exit(9)
