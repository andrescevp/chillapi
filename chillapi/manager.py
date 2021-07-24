import os
from typing import List

import inflect

from . import ApiManager
from .app.config import ApiConfig
from .endpoints.sql import create_sql_endpoint_class
from .endpoints.tables import (
    create_delete_list_endpoint_class,
    create_delete_single_endpoint_class,
    create_get_list_endpoint_class,
    create_get_single_endpoint_class,
    create_post_list_endpoint_class,
    create_post_single_endpoint_class,
    create_put_list_endpoint_class,
    create_put_single_endpoint_class,
)
from .exceptions.api_manager import ConfigError
from .swagger.http import AutomaticResource
from .swagger.schemas import create_swagger_type_from_dict

inflector = inflect.engine()
created_endpoint_used_names = []


class FlaskSqlApiManager(ApiManager):
    """ """

    def __init__(self, config: ApiConfig):
        self.config = config

    def create_api(self, api):
        """

        :param api:

        """
        for source_key in self.config.database:
            for i, sql_endpoint in enumerate(self.config.database[source_key]["sql"]):
                sql = sql_endpoint["sql"]
                duplicated_name_postfix = "_SQL"
                self.create_sql_endpoint(api, duplicated_name_postfix, i, sql, sql_endpoint, source_key)

        for source_key in self.config.database:
            for i, sql_endpoint in enumerate(self.config.database[source_key]["templates"]):
                template = sql_endpoint["template"]
                if template.startswith("."):
                    template = f'{os.getcwd()}{template.lstrip(".")}'
                template = os.path.realpath(template)
                with open(template) as sql_template:
                    sql = sql_template.read()
                duplicated_name_postfix = "_TSQL"

                self.create_sql_endpoint(api, duplicated_name_postfix, i, sql, sql_endpoint, source_key)

    def create_sql_endpoint(self, api, duplicated_name_postfix, i, sql, sql_endpoint, source_key):
        """

        :param api:
        :param duplicated_name_postfix:
        :param i:
        :param sql:
        :param sql_endpoint:

        """
        method = sql_endpoint["method"]
        name = sql_endpoint["name"]
        tags = [name]
        request_schema = None
        response_schema = None
        query_parameters = {}
        description = ""
        if "description" in sql_endpoint:
            description = sql_endpoint["description"]
        if "tags" in sql_endpoint:
            tags = sql_endpoint["tags"]
        if "request_schema" in sql_endpoint:
            request_schema = sql_endpoint["request_schema"]
        if "response_schema" in sql_endpoint:
            response_schema = sql_endpoint["response_schema"]
        if "query_parameters" in sql_endpoint:
            query_parameters = sql_endpoint["query_parameters"]
        if name in created_endpoint_used_names:
            name = f"{name}{method.capitalize()}{i}{duplicated_name_postfix}"
        created_endpoint_used_names.append(name)
        if method in ["POST", "PUT"] and request_schema is None:
            raise ConfigError(f"SQL Endpoints POST/PUT requires a request schema. Name: {name}")
        url = sql_endpoint["url"]
        if request_schema:
            request_schema = create_swagger_type_from_dict(f"{name}SqlRequestSchema", request_schema)
        if response_schema:
            response_schema = create_swagger_type_from_dict(f"{name}SqlRequestSchema", response_schema)
        sql_endpoint_class = create_sql_endpoint_class(
            name,
            method,
            url,
            sql,
            self.config.repository[source_key],
            query_parameters,
            tags,
            request_schema,
            response_schema,
            description,
        )

        api.add_resource(sql_endpoint_class, sql_endpoint_class.route, endpoint=sql_endpoint_class.endpoint)


class FlaskTableApiManager(ApiManager):
    """ """

    def __init__(self, config: ApiConfig):
        self.config = config

    def create_get_single_endpoint(
        self,
        table: dict,
        endpoint: str,
        source_key: str,
        action: str,
        allowed_columns: List,
        excluded_columns: List,
        allowed_columns_map: dict,
        extensions: dict,
    ):
        """

        :param table: dict:
        :param endpoint: str:
        :param action: str:
        :param allowed_columns: List:
        :param excluded_columns: List:
        :param allowed_columns_map: dict:
        :param extensions: dict:

        """

        return create_get_single_endpoint_class(table, allowed_columns, allowed_columns_map, extensions, self.config.repository[source_key])

    def create_put_single_endpoint(
        self,
        table: dict,
        endpoint: str,
        source_key: str,
        action: str,
        allowed_columns: List,
        excluded_columns: List,
        allowed_columns_map: dict,
        extensions: dict,
    ):
        """

        :param table: dict:
        :param endpoint: str:
        :param action: str:
        :param allowed_columns: List:
        :param excluded_columns: List:
        :param allowed_columns_map: dict:
        :param extensions: dict:

        """

        return create_put_single_endpoint_class(table, allowed_columns, allowed_columns_map, extensions, self.config.repository[source_key])

    def create_post_single_endpoint(
        self,
        table: dict,
        endpoint: str,
        source_key: str,
        action: str,
        allowed_columns: List,
        excluded_columns: List,
        allowed_columns_map: dict,
        extensions: dict,
    ):
        """

        :param table: dict:
        :param endpoint: str:
        :param action: str:
        :param allowed_columns: List:
        :param excluded_columns: List:
        :param allowed_columns_map: dict:
        :param extensions: dict:

        """

        return create_post_single_endpoint_class(table, allowed_columns, allowed_columns_map, extensions, self.config.repository[source_key])

    def create_delete_single_endpoint(
        self,
        table: dict,
        endpoint: str,
        source_key: str,
        action: str,
        allowed_columns: List,
        excluded_columns: List,
        allowed_columns_map: dict,
        extensions: dict,
    ):
        """

        :param table: dict:
        :param endpoint: str:
        :param action: str:
        :param allowed_columns: List:
        :param excluded_columns: List:
        :param allowed_columns_map: dict:
        :param extensions: dict:

        """
        return create_delete_single_endpoint_class(table, allowed_columns, allowed_columns_map, extensions, self.config.repository[source_key])

    def create_get_list_endpoint(
        self,
        table: dict,
        endpoint: str,
        source_key: str,
        action: str,
        allowed_columns: List,
        excluded_columns: List,
        allowed_columns_map: dict,
        extensions: dict,
    ):
        """

        :param table: dict:
        :param endpoint: str:
        :param action: str:
        :param allowed_columns: List:
        :param excluded_columns: List:
        :param allowed_columns_map: dict:
        :param extensions: dict:

        """
        return create_get_list_endpoint_class(
            table,
            allowed_columns,
            allowed_columns_map,
            extensions,
            self.config.repository[source_key],
        )

    def create_put_list_endpoint(
        self,
        table: dict,
        endpoint: str,
        source_key: str,
        action: str,
        allowed_columns: List,
        excluded_columns: List,
        allowed_columns_map: dict,
        extensions: dict,
    ):
        """

        :param table: dict:
        :param endpoint: str:
        :param action: str:
        :param allowed_columns: List:
        :param excluded_columns: List:
        :param allowed_columns_map: dict:
        :param extensions: dict:

        """
        return create_put_list_endpoint_class(
            table,
            allowed_columns,
            allowed_columns_map,
            extensions,
            self.config.repository[source_key],
        )

    def create_post_list_endpoint(
        self,
        table: dict,
        endpoint: str,
        source_key: str,
        action: str,
        allowed_columns: List,
        excluded_columns: List,
        allowed_columns_map: dict,
        extensions: dict,
    ):
        """

        :param table: dict:
        :param endpoint: str:
        :param action: str:
        :param allowed_columns: List:
        :param excluded_columns: List:
        :param allowed_columns_map: dict:
        :param extensions: dict:

        """
        return create_post_list_endpoint_class(
            table,
            allowed_columns,
            allowed_columns_map,
            extensions,
            self.config.repository[source_key],
        )

    def create_delete_list_endpoint(
        self,
        table: dict,
        endpoint: str,
        source_key: str,
        action: str,
        allowed_columns: List,
        excluded_columns: List,
        allowed_columns_map: dict,
        extensions: dict,
    ):
        """

        :param table: dict:
        :param endpoint: str:
        :param action: str:
        :param allowed_columns: List:
        :param excluded_columns: List:
        :param allowed_columns_map: dict:
        :param extensions: dict:

        """
        return create_delete_list_endpoint_class(
            table,
            allowed_columns,
            allowed_columns_map,
            extensions,
            self.config.repository[source_key],
        )

    def create_api(self, api):
        """

        :param api:

        """
        for source_key in self.config.database:
            for table in self.config.database[source_key]["tables"]:
                for endpoint, actions in table["api_endpoints"].items():
                    for action in actions:
                        _create_method = f"create_{endpoint.lower()}_{action.lower()}_endpoint"
                        _create = getattr(self, _create_method, None)

                        if _create is None:
                            raise ConfigError(f"There is not {_create_method}")
                        model_name = table["model_name"]
                        table_columns = table["columns"]

                        table_columns_excluded = table["fields_excluded"][endpoint][action] if endpoint != "DELETE" else {}
                        table_extensions = self.config.extensions.tables[source_key][model_name]
                        allowed_columns = [x for x in table_columns.keys() if x not in table_columns_excluded]

                        allowed_columns_map = {x: table["columns"][x] for x in table["columns"].keys() if x in allowed_columns}
                        _endpoint: AutomaticResource = _create(
                            **{
                                "table": table,
                                "endpoint": endpoint,
                                "action": action,
                                "allowed_columns": allowed_columns,
                                "excluded_columns": table_columns_excluded,
                                "allowed_columns_map": allowed_columns_map,
                                "extensions": table_extensions,
                                "source_key": source_key,
                            }
                        )

                        api.add_resource(
                            _endpoint,
                            _endpoint.route,
                            endpoint=_endpoint.endpoint,
                            resource_class_kwargs={
                                "before_request": self.config.extensions.tables[source_key][model_name]["before_request"],
                                "before_response": self.config.extensions.tables[source_key][model_name]["before_response"],
                                "after_response": self.config.extensions.tables[source_key][model_name]["after_response"],
                            },
                        )


class FlaskApiManager(ApiManager):
    """ """

    def __init__(self, config: ApiConfig):
        self.sql_manager = FlaskSqlApiManager(config)
        self.table_manager = FlaskTableApiManager(config)

    def create_api(self, api):
        """

        :param api:

        """
        self.table_manager.create_api(api)
        self.sql_manager.create_api(api)
