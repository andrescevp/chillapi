from abc import ABC, abstractmethod
from typing import List

from sqlalchemy.engine import CursorResult, Inspector
from sqlalchemy.orm.scoping import ScopedSession

from .database import _ALLOWED_DRIVERS
from .exceptions.api_manager import ColumnNotExist, ConfigError


class Repository(ABC):
    """ """

    def __init__(self, db: ScopedSession):
        self.db = db
        driver = self.db.bind.dialect.dbapi.__name__
        if driver not in _ALLOWED_DRIVERS.keys():
            raise ConfigError(f"{driver} driver not allowed")
        self.db_dialect = _ALLOWED_DRIVERS[driver]

    @abstractmethod
    def execute(self, sql, params=None) -> CursorResult:
        """

        :param sql: param params:  (Default value = None)
        :param params:  (Default value = None)

        """
        pass

    @abstractmethod
    def execute_insert(self, sql, params=None) -> CursorResult:
        """

        :param sql: param params:  (Default value = None)
        :param params:  (Default value = None)

        """
        pass

    @abstractmethod
    def fetch_by(self, table: str, columns: List[str], filters: dict, params=None):
        """

        :param table: str:
        :param columns: List[str]:
        :param filters: dict:
        :param params: Default value = None)
        :param table: str:
        :param columns: List[str]:
        :param filters: dict:

        """
        pass

    @abstractmethod
    def insert(self, table: str, columns: List[str], params: dict, returning: bool = True, returning_field: str = "*") -> CursorResult:
        """

        :param table: str:
        :param columns: List[str]:
        :param params: dict:
        :param returning: bool:  (Default value = True)
        :param returning_field: str:  (Default value = "*")
        :param table: str:
        :param columns: List[str]:
        :param params: dict:
        :param returning: bool:  (Default value = True)
        :param returning_field: str:  (Default value = "*")

        """
        pass

    @abstractmethod
    def insert_batch(self, table: str, columns: List[str], params: List, returning: bool = True, returning_field: str = "*") -> List:
        """

        :param table: str:
        :param columns: List[str]:
        :param params: List:
        :param returning: bool:  (Default value = True)
        :param returning_field: str:  (Default value = "*")
        :param table: str:
        :param columns: List[str]:
        :param params: List:
        :param returning: bool:  (Default value = True)
        :param returning_field: str:  (Default value = "*")

        """
        pass

    @abstractmethod
    def update_batch(self, table: str, params: List, where_field: str = "id") -> List:
        """

        :param table: str:
        :param params: List:
        :param where_field: str:  (Default value = "id")
        :param table: str:
        :param params: List:
        :param where_field: str:  (Default value = "id")

        """
        pass

    @abstractmethod
    def delete_batch(self, table: str, ids: List, where_field: str = "id") -> List:
        """

        :param table: str:
        :param ids: List:
        :param where_field: str:  (Default value = "id")
        :param table: str:
        :param ids: List:
        :param where_field: str:  (Default value = "id")

        """
        pass

    @abstractmethod
    def insert_record(self, table: str, columns: List[str], params: dict, returning: bool = True, returning_field: str = "*") -> int:
        """

        :param table: str:
        :param columns: List[str]:
        :param params: dict:
        :param returning: bool:  (Default value = True)
        :param returning_field: str:  (Default value = "*")
        :param table: str:
        :param columns: List[str]:
        :param params: dict:
        :param returning: bool:  (Default value = True)
        :param returning_field: str:  (Default value = "*")

        """
        pass

    @abstractmethod
    def update_record(self, table: str, where_field: str, where_value: str, params: dict) -> CursorResult:
        """

        :param table: str:
        :param where_field: str:
        :param where_value: str:
        :param params: dict:
        :param table: str:
        :param where_field: str:
        :param where_value: str:
        :param params: dict:

        """
        pass

    @abstractmethod
    def delete_record(self, table: str, where_field: str, where_field_id) -> CursorResult:
        """

        :param table: str:
        :param where_field: str:
        :param where_field_id:
        :param table: str:
        :param where_field: str:

        """
        pass


class Extension(ABC, dict):
    """ """

    def execute(self, *args):
        """

        :param *args:

        """
        method_name = getattr(args, "method")
        if method_name == "execute":
            raise Exception("You can not call myself")
        method = getattr(self, getattr(args, "method"))
        return method(getattr(args, "args"))


class TableExtension(Extension):
    """ """

    enabled: bool = False
    table: str = None
    config: dict = None
    repository: Repository = None
    inspector: Inspector

    def __init__(self, config: dict, columns: dict = None, repository: Repository = None, table: str = None, inspector: Inspector = None):
        super().__init__()
        self.inspector = inspector
        self.columns = columns
        self.repository = repository
        self.config = config
        self.table = table
        self.enabled = self.config["enable"]

    def validate(self):
        """ """
        if not self.enabled:
            return True
        _default_field = self.config["default_field"]

        if _default_field not in self.columns.keys():
            raise ColumnNotExist(f'{self.__class__.__name__}: "{_default_field}" not found on table "{self.table}" ')

        return True


class AuditLog(ABC, dict):
    """ """

    request_id: str = None
    prev_request_id: str = None
    date: str = None
    message: str = None

    @abstractmethod
    def for_json(self) -> dict:
        """ """
        pass


class AuditLogHandler(Extension):
    """ """

    @abstractmethod
    def log(self, log: AuditLog):
        """

        :param log: AuditLog:
        :param log: AuditLog:

        """
        pass

    def execute(self, *args):
        """

        :param *args:

        """
        self.log(getattr(args, "log"))


class AttributeDict(dict):
    """ """

    __slots__ = ()
    __getattr__ = dict.__getitem__
    __setattr__ = dict.__setitem__
