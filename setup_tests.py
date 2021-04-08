import os
import unittest

from alembic import command
from alembic.config import Config
from chillapi.logger.app_loggers import logger

dir_path = os.path.dirname(os.path.realpath(__file__))

os.environ.setdefault('__CHILLAPI_SETUP_TESTING__', 'true')
os.environ.setdefault('__CHILLAPI_SETUP_TESTING_DB_DSN__', 'postgresql://root:root@localhost/chillapi')

def run_migrations(dsn: str) -> None:
    logger.info('Running TEST DB migrations on %r', dsn)
    alembic_cfg = Config(file_ = f'{dir_path}/postgres.alembic.ini')
    alembic_cfg.set_main_option('sqlalchemy.url', dsn)
    command.upgrade(alembic_cfg, 'head')


run_migrations(os.environ.get('__CHILLAPI_SETUP_TESTING_DB_DSN__'))

# sqlite_file = f'{dir_path}/var/sqlite.db'
# if os.path.exists(sqlite_file):
#     os.remove(sqlite_file)

# alembic_args = [
#         f'-c{dir_path}/postgres_localhost.alembic.ini',
#         'upgrade', 'head'
#         ]
#
# alembic.config.main(argv = alembic_args)

loader = unittest.TestLoader()
tests = loader.discover(f'{dir_path}/tests')
testRunner = unittest.runner.TextTestRunner()
testRunner.run(tests)
