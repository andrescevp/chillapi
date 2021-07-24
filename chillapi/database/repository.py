from typing import List

import simplejson
import sqlalchemy
from sqlalchemy import text
from sqlalchemy.engine import CursorResult

from ..abc import Repository
from ..database import DB_DIALECT_SQLITE
from ..database.query_builder import create_delete, create_insert, create_select_filtered_query, create_update
from ..logger.app_loggers import logger

DB_DIALECT_POSTGRES = "postgres"

_MAGIC_QUERIES = {
    DB_DIALECT_POSTGRES: {
        "get_ids_not_in_table_from_list": lambda x: f"""
            SELECT id
            FROM (VALUES({'),('.join(x['values'])})) V({x['id_field']})
            EXCEPT
            SELECT {x['id_field']}
            FROM  {x['table']}
            {x['where']}
        """
    },
    DB_DIALECT_SQLITE: {
        "get_ids_not_in_table_from_list": lambda x: f"""
            select t.id
from (
  values ({'),('.join(x['values'])})
) as t(id)
  left join {x['table']} i on i.{x['id_field']} = t.id
where i.{x['id_field']} is null;
        """
    },
}


class DataRepository(Repository):
    """ """

    def adapt_params(self, params):
        """

        :param params:

        """
        adapted_params = dict({})
        for key, value in params.items():
            adapted_params[key] = value
            if type(value) == dict:
                adapted_params[key] = str(simplejson.dumps(value))
        return adapted_params

    def execute(self, sql, params=None) -> CursorResult:
        """

        :param sql:
        :param params:  (Default value = None)

        """
        try:
            r = self.db.execute(text(sql), params)
        except sqlalchemy.exc.DatabaseError as e:
            logger.critical(e)
            raise e
        except Exception as e:
            logger.critical(e)
            raise e
        return r

    def execute_insert(self, sql, params=None) -> CursorResult:
        """

        :param sql:
        :param params:  (Default value = None)

        """
        try:
            r = self.db.execute(sql, params)
            self.db.commit()
        except sqlalchemy.exc.DatabaseError as e:
            logger.critical(e)
            self.db.rollback()
            raise e
        except Exception as e:
            logger.critical(e)
            self.db.rollback()
            raise e
        return r

    def fetch_by(self, table: str, columns: List[str], filters: dict, params=None):
        """

        :param table: str:
        :param columns: List[str]:
        :param filters: dict:
        :param params:  (Default value = None)

        """
        sql = create_select_filtered_query(table, columns, filters)
        return self.execute(sql, params)

    def insert(self, table: str, columns: List[str], params: dict, returning: bool = True, returning_field: str = "*") -> CursorResult:
        """

        :param table: str:
        :param columns: List[str]:
        :param params: dict:
        :param returning: bool:  (Default value = True)
        :param returning_field: str:  (Default value = "*")

        """
        adapted_params = self.adapt_params(params)
        params_keys = adapted_params.keys()
        select_columns = [c for c in columns if c in params_keys]
        sql = create_insert(table, select_columns) + f"{' RETURNING ' + returning_field if returning is True else ''}"
        return self.execute(sql, adapted_params)

    def insert_batch(self, table: str, columns: List[str], params: List, returning: bool = True, returning_field: str = "*") -> List:
        """

        :param table: str:
        :param columns: List[str]:
        :param params: List:
        :param returning: bool:  (Default value = True)
        :param returning_field: str:  (Default value = "*")

        """
        adapted_params = [self.adapt_params(param) for param in params]
        params_keys = adapted_params[0].keys()
        select_columns = [c for c in columns if c in params_keys]

        returning_stmt = f"RETURNING {returning_field}"

        if self.db_dialect != DB_DIALECT_POSTGRES:
            returning_stmt = ""
        sql = create_insert(table, select_columns) + returning_stmt

        insert_result = self.execute(sql, adapted_params)

        return insert_result.rowcount

    def update_batch(self, table: str, params: List, where_field: str = "id") -> List:
        """

        :param table: str:
        :param params: List:
        :param where_field: str:  (Default value = "id")

        """
        adapted_params = [self.adapt_params(param) for param in params]
        for i, _params in enumerate(adapted_params):
            where_value = _params[where_field]
            execute_params = _params.copy()
            del _params[where_field]
            sql = create_update(table, _params, {where_field: {"op": "=", "value": where_value}})
            self.execute(sql, execute_params)

        return []

    def delete_batch(self, table: str, ids: List, where_field: str = "id") -> List:
        """

        :param table: str:
        :param ids: List:
        :param where_field: str:  (Default value = "id")

        """
        for i, _id in enumerate(ids):
            sql = create_delete(table, {where_field: {"op": "=", "value": _id}})
            self.execute(sql, {where_field: _id})

        return []

    def insert_record(self, table: str, columns: List[str], params: dict, returning: bool = True, returning_field: str = "*") -> int:
        """

        :param table: str:
        :param columns: List[str]:
        :param params: dict:
        :param returning: bool:  (Default value = True)
        :param returning_field: str:  (Default value = "*")

        """
        adapted_params = self.adapt_params(params)
        params_keys = adapted_params.keys()
        select_columns = [c for c in columns if c in params_keys]
        returning_stmt = f"RETURNING {returning_field}"
        if self.db_dialect != DB_DIALECT_POSTGRES:
            returning_stmt = ""
        sql = create_insert(table, select_columns) + returning_stmt
        insert_result = self.execute(sql, adapted_params)

        if self.db_dialect == DB_DIALECT_SQLITE:
            return insert_result.lastrowid
        # if self.db_dialect == DB_DIALECT_MS_SQL_SERVER:
        #     return insert_result.fetchone()[0]
        # if self.db_dialect == DB_DIALECT_MARIADB_MYSQL:
        #     inserted_id = self.execute('SELECT LAST_INSERT_ID()')
        #     return inserted_id.fetchone()[0]

        return insert_result.fetchone()[0]

    def update_record(self, table: str, where_field: str, where_value: str, params: dict) -> CursorResult:
        """

        :param table: str:
        :param where_field: str:
        :param where_value: str:
        :param params: dict:

        """
        adapted_params = self.adapt_params(params)
        sql = create_update(table, adapted_params, {where_field: {"op": "=", "value": where_value}})
        return self.execute(sql, {**adapted_params, **{where_field: where_value}})

    def delete_record(self, table: str, where_field: str, where_field_id) -> CursorResult:
        """

        :param table: str:
        :param where_field: str:
        :param where_field_id:

        """

        sql = create_delete(table, {where_field: {"op": "=", "value": where_field_id}})
        return self.execute(sql, {where_field: where_field_id})
