import logging
import os

import yaml
from dotenv import load_dotenv
from pathlib import Path
from pykwalify.core import Core
from pykwalify.errors import SchemaError as YamlSchemaError

from chillapi.exceptions.api_manager import ConfigError

env_path = Path(os.getcwd()) / ".env"
load_dotenv(dotenv_path=env_path)
from chillapi.logger.app_loggers import formatter, stout_handler


def read_yaml(file):
    with open(file) as file:
        yaml_file = yaml.load(file, Loader=yaml.FullLoader)
    return yaml_file


def parse_config(app_config: dict):
    if 'logger' in app_config['app']:
        logger_conf = app_config['app']['logger']
        if logger_conf['package'] not in _virtual_modules_map.keys():
            _virtual_modules_map[logger_conf['package']] = []
        _virtual_modules_map[logger_conf['package']].append(logger_conf['audit_log_handler'])


CONFIG_FILE = 'api.yaml'
SCHEMA_CONFIG_FILE = 'api.schema.yaml'

c = Core(source_file=CONFIG_FILE, schema_files=[SCHEMA_CONFIG_FILE])
try:
    c.validate(raise_exception=True)
except YamlSchemaError as e:
    raise ConfigError(f'Api config file config error. {e.msg}')

_virtual_modules_map = {}
api_config = read_yaml(CONFIG_FILE)
# simplejson.dump(api_config, open('api.json', 'w'))

def _set_logger_config(logger_config: dict, audit_logger: dict = None, debug: bool = False):
    log_file_handler = None
    for logger_name, config in logger_config.items():
        if logger_name == 'audit_logger' and debug is False:
            log_null_handler = logging.NullHandler()
            logging.getLogger(logger_name).removeHandler(stout_handler)
            logging.getLogger(logger_name).addHandler(log_null_handler)
        if logger_name == 'audit_logger' and audit_logger and debug is False:
            continue
        if logger_name == 'sqlalchemy':
            logger_name = 'sqlalchemy.engine'

        if 'output' in config and config['output'] != 'stdout':
            if log_file_handler is None:
                log_file_handler = logging.FileHandler(config['output'])
                log_file_handler.setFormatter(formatter)
            logging.getLogger(logger_name).removeHandler(stout_handler)
            logging.getLogger(logger_name).addHandler(log_file_handler)
        if 'level' in config:
            logging.getLogger(logger_name).setLevel(int(config['level']))


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


# parse_config(api_config)
