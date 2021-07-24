from typing import List

import inflect
from flask import request

from ..app.swagger_schema import swagger
from ..database.repository import DataRepository
from ..swagger.http import AutomaticResource, ResourceResponse
from ..swagger.schemas import get_query_endpoint_schema
from ..swagger.utils import get_error_swagger_schema, get_not_found_swagger_schema

error_swagger_schema = get_error_swagger_schema()
not_found_swagger_schema = get_not_found_swagger_schema()

inflector = inflect.engine()


def create_sql_endpoint_class(
    name: str,
    method: str,
    url: str,
    sql: str,
    repository: DataRepository,
    query_parameters: List,
    tags: List,
    request_schema: type = None,
    response_schema: dict = None,
    description: str = None,
    is_from_template: bool = False,
):
    """

    :param name: str:
    :param method: str:
    :param url: str:
    :param sql: str:
    :param repository: DataRepository:
    :param query_parameters: List:
    :param tags: List:
    :param request_schema: type:  (Default value = None)
    :param response_schema: dict:  (Default value = None)
    :param description: str:  (Default value = None)
    :param is_from_template: bool:  (Default value = False)

    """
    schema = get_query_endpoint_schema(name, tags, query_parameters, description, request_schema, response_schema)

    class QueryEndpoint(AutomaticResource):
        """ """

        route = f'/{url.lstrip("/")}'
        endpoint = f'/{name}{"Template" if is_from_template else ""}QueryEndpoint'

        # representations = schema

        def request(self, **args) -> ResourceResponse:
            """

            :param **args:

            """
            query = args["query"]
            response = ResourceResponse()
            record = repository.execute(sql, query)
            response.response = record.fetchall()
            return response

        if method == "GET":

            @swagger.doc(schema)
            def get(self, **kwargs):
                """

                :param **kwargs:

                """
                query = {**{k: v for k, v in request.args.items()}, **kwargs}
                return self.process_request(query=query)

        if method == "POST":

            @swagger.doc(schema)
            def post(self, **kwargs):
                """

                :param **kwargs:

                """
                query = {**{k: v for k, v in request.args.items()}, **kwargs}
                query = {**query, **request.json}
                return self.process_request(query=query)

        if method == "PUT":

            @swagger.doc(schema)
            def put(self, **kwargs):
                """

                :param **kwargs:

                """
                query = {**{k: v for k, v in request.args.items()}, **kwargs}
                query = {**query, **request.json}
                return self.process_request(query=query)

        if method == "DELETE":

            @swagger.doc(schema)
            def delete(self, **kwargs):
                """

                :param **kwargs:

                """
                query = {**{k: v for k, v in request.args.items()}, **kwargs}
                query = {**query, **request.json}
                return self.process_request(query=query)

    QueryEndpoint.__name__ = QueryEndpoint.endpoint
    return QueryEndpoint
