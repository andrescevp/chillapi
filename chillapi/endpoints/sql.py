from typing import List

from flask import request
from flask_restful_swagger_3 import swagger
import inflect

from chillapi.database.repository import DataRepository
from chillapi.swagger.http import AutomaticResource, ResourceResponse
from chillapi.swagger.schemas import get_query_endpoint_schema
from chillapi.swagger.utils import get_revisable_response_swagger_schema, get_error_swagger_schema, get_not_found_swagger_schema

revisable_response_swagger_schema = get_revisable_response_swagger_schema()
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
        is_from_template : bool = False
):
    schema = get_query_endpoint_schema(name, tags, query_parameters, description, request_schema, response_schema)

    class QueryEndpoint(AutomaticResource):
        route = f'/{url.lstrip("/")}'
        endpoint = f'/{name}{"Template" if is_from_template else ""}QueryEndpoint'
        # representations = schema

        def request(self, **args) -> ResourceResponse:
            query = args['query']
            response = ResourceResponse()
            record = repository.execute(sql, query)
            response.response = record.fetchall()
            return response

        if method == 'GET':
            @swagger.doc(schema)
            def get(self, **kwargs):
                query = {**{k: v for k, v in request.args.items()}, **kwargs}
                return self.process_request(query=query)
        if method == 'POST':
            @swagger.doc(schema)
            def post(self, **kwargs):
                query = {**{k: v for k, v in request.args.items()}, **kwargs}
                query = {**query, **request.json}
                return self.process_request(query=query)
        if method == 'PUT':
            @swagger.doc(schema)
            def put(self, **kwargs):
                query = {**{k: v for k, v in request.args.items()}, **kwargs}
                query = {**query, **request.json}
                return self.process_request(query=query)
        if method == 'DELETE':
            @swagger.doc(schema)
            def delete(self, **kwargs):
                query = {**{k: v for k, v in request.args.items()}, **kwargs}
                query = {**query, **request.json}
                return self.process_request(query=query)

    QueryEndpoint.__name__ = QueryEndpoint.endpoint
    return QueryEndpoint
