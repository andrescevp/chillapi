from abc import ABC, abstractmethod
from typing import List

from sqlalchemy.engine import CursorResult, Inspector
from sqlalchemy.orm.scoping import ScopedSession

from chillapi.database import _ALLOWED_DRIVERS
from chillapi.exceptions.api_manager import ColumnNotExist, ConfigError


class Repository(ABC):
    def __init__(self, db: ScopedSession):
        self.db = db
        driver = self.db.bind.dialect.dbapi.__name__
        if driver not in _ALLOWED_DRIVERS.keys():
            raise ConfigError(f'{driver} driver not allowed')
        self.db_dialect = _ALLOWED_DRIVERS[driver]

    @abstractmethod
    def execute(self, sql, params = None, commit: bool = True) -> CursorResult:
        pass

    @abstractmethod
    def execute_insert(self, sql, params = None) -> CursorResult:
        pass

    @abstractmethod
    def fetch_by(self, table: str, columns: List[str], filters: dict, params = None):
        pass

    @abstractmethod
    def insert(self, table: str, columns: List[str], params: dict,
               returning: bool = True, returning_field: str = "*") -> CursorResult:
        pass

    @abstractmethod
    def insert_batch(self, table: str, columns: List[str], params: List,
                     returning: bool = True, returning_field: str = "*") -> List:
        pass

    @abstractmethod
    def update_batch(self, table: str, params: List, where_field: str = 'id') -> List:
        pass

    @abstractmethod
    def delete_batch(self, table: str, ids: List, where_field: str = 'id') -> List:
        pass

    @abstractmethod
    def insert_record(self, table: str, columns: List[str], params: dict,
                      returning: bool = True, returning_field: str = "*") -> int:
        pass

    @abstractmethod
    def update_record(self, table: str, where_field: str, where_value: str, params: dict) -> CursorResult:
        pass

    @abstractmethod
    def delete_record(self, table: str, where_field: str, where_field_id) -> CursorResult:
        pass


class Extension(ABC, dict):
    def execute(self, *args):
        method_name = getattr(args, 'method')
        if method_name == 'execute':
            raise Exception('You can not call myself')
        method = getattr(self, getattr(args, 'method'))
        return method(getattr(args, 'args'))


class TableExtension(Extension):
    enabled: bool = False
    table: str = None
    config: dict = None
    repository: Repository = None
    inspector: Inspector

    def __init__(self, config: dict, columns: dict = None, repository: Repository = None, table: str = None,
                 inspector: Inspector = None):
        self.inspector = inspector
        self.columns = columns
        self.repository = repository
        self.config = config
        self.table = table
        self.enabled = self.config['enable']

    def validate(self):
        if not self.enabled:
            return True
        _default_field = self.config['default_field']

        if _default_field not in self.columns.keys():
            raise ColumnNotExist(f'{self.__class__.__name__}: "{_default_field}" not found on table "{self.table}" ')

        return True


class AuditLog(ABC, dict):
    request_id: str = None
    prev_request_id: str = None
    date: str = None
    message: str = None

    @abstractmethod
    def for_json(self) -> dict:
        pass


class AuditLogHandler(Extension):
    @abstractmethod
    def log(self, log: AuditLog):
        pass

    def execute(self, *args):
        self.log(getattr(args, 'log'))
