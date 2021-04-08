import os
from typing import List

from schemainspect import get_inspector
from sqlalchemy.orm import scoped_session
from sqlbag import S
import inflect

from chillapi.exceptions.api_manager import ConfigError
from chillapi.app.forms import create_form_class, generate_form_swagger_schema_from_form
from chillapi import SingletonMeta, ApiManager
from chillapi.database.repository import DataRepository
from chillapi.swagger.schemas import create_swagger_type_from_dict
from chillapi.endpoints.sql import create_sql_endpoint_class
from chillapi.endpoints.tables import create_get_single_endpoint_class, create_put_single_endpoint_class, \
    create_post_single_endpoint_class, create_delete_single_endpoint_class, create_get_list_endpoint_class, \
    create_put_list_endpoint_class, create_post_list_endpoint_class, create_delete_list_endpoint_class
from chillapi.endpoints.tables_utils import columns_map_filter_allowed_columns
from mergedeep import merge as dict_deepmerge

inflector = inflect.engine()
created_endpoint_used_names = []


class FlaskTableApiManager(ApiManager, metaclass=SingletonMeta):
    def __init__(
            self,
            name: str,
            schema: str,
            fields_excluded: dict,
            api_endpoints: dict,
            extensions: dict,
            tables: List,
            sql_entrypoints: List,
            sql_templates: List,
            db: scoped_session,
            db_url: str,
    ):
        self.extensions = extensions
        self.sql_templates = sql_templates
        self.sql_endpoints = sql_entrypoints
        self.db_url = db_url
        self.db = db
        self.tables = tables
        self.schema = schema
        self.name = name
        self.repository = DataRepository(db)
        self.fields_excluded = fields_excluded
        self.api_endpoints = api_endpoints
        with S(self.db_url) as s:
            self.db_inspector = get_inspector(s)

    def get_columns_table_details(self, table_name):
        return self.db_inspector.tables[f'"{self.schema}"."{table_name}"'].columns

    def create_api(self, api):
        table_default_fields_excluded = []
        if 'all' in self.fields_excluded:
            table_default_fields_excluded = self.fields_excluded['all'].copy()

        for i, table in enumerate(self.tables):
            self.create_table_endpoint(api, i, table, table_default_fields_excluded)

        for i, sql_endpoint in enumerate(self.sql_endpoints):
            sql = sql_endpoint['sql']
            duplicated_name_postfix = '_SQL'
            self.create_sql_endpoint(api, duplicated_name_postfix, i, sql, sql_endpoint)

        for i, sql_endpoint in enumerate(self.sql_templates):
            template = sql_endpoint['template']
            if template.startswith('.'):
                template = f'{os.getcwd()}{template.lstrip(".")}'
            template = os.path.realpath(template)
            with open(template) as sql_template:
                sql = sql_template.read()
            duplicated_name_postfix = '_TSQL'

            self.create_sql_endpoint(api, duplicated_name_postfix, i, sql, sql_endpoint)

    def create_table_endpoint(self, api, i, table, table_default_fields_excluded):
        table_name = table['name']
        table_id_field = table['id_field'] if 'id_field' in table and table['id_field'] is not None else 'id'
        # get api entity name
        model_name = table['alias'] if table['alias'] is not None else table_name
        if model_name in created_endpoint_used_names:
            model_name = f'{model_name}{i}'
        table_columns = self.get_columns_table_details(table['name'])
        columns_names = [c for c in table_columns]
        columns_map = {name: v for name, v in table_columns.items()}
        if 'fields_excluded' in table and 'all' in table['fields_excluded']:
            table_default_fields_excluded = dict_deepmerge({}, self.fields_excluded['all'],
                                                           table['fields_excluded']['all'])
            table_default_fields_excluded = [c for c in table_default_fields_excluded if c in columns_names]

        table_endpoints = self.api_endpoints.copy()
        if 'api_endpoints' in table and len(table['api_endpoints']) > 0:
            table_endpoints = table['api_endpoints']

        table_extensions = self.extensions.copy()
        if 'extensions' in table:
            table_extensions = dict_deepmerge({}, self.extensions, table['extensions'])

        for endpoint, actions in table_endpoints.items():
            for action in actions:
                request_fields_excluded = self.get_fields_excluded(
                    action,
                    columns_names,
                    endpoint,
                    table,
                    table_default_fields_excluded
                )

                response_fields_excluded = request_fields_excluded  # on some point this has to be different?

                _create_method = f'create_{endpoint.lower()}_{action.lower()}_endpoint'
                _create = getattr(self, _create_method, None)

                if _create is None:
                    raise ConfigError(f'There is not {_create_method}')

                _endpoint_args = self.get_table_endpont_creation_args(action, columns_map, endpoint, model_name,
                                                                      request_fields_excluded,
                                                                      response_fields_excluded, table_id_field,
                                                                      table_name, table_extensions)

                _endpoint = _create(**_endpoint_args)

                api.add_resource(_endpoint, _endpoint.route,
                                 endpoint=_endpoint.endpoint)

    def create_sql_endpoint(self, api, duplicated_name_postfix, i, sql, sql_endpoint):
        method = sql_endpoint['method']
        name = sql_endpoint['name']
        tags = [name]
        request_schema = None
        response_schema = None
        query_parameters = {}
        description = ''
        if 'description' in sql_endpoint:
            description = sql_endpoint['description']
        if 'tags' in sql_endpoint:
            tags = sql_endpoint['tags']
        if 'request_schema' in sql_endpoint:
            request_schema = sql_endpoint['request_schema']
        if 'response_schema' in sql_endpoint:
            response_schema = sql_endpoint['response_schema']
        if 'query_parameters' in sql_endpoint:
            query_parameters = sql_endpoint['query_parameters']
        if name in created_endpoint_used_names:
            name = f'{name}{method.capitalize()}{i}{duplicated_name_postfix}'
        created_endpoint_used_names.append(name)
        if method in ['POST', 'PUT'] and request_schema is None:
            raise ConfigError(f'SQL Endpoints POST/PUT requires a request schema. Name: {name}')
        url = sql_endpoint['url']
        if request_schema:
            request_schema = create_swagger_type_from_dict(f'{name}SqlRequestSchema', request_schema)
        if response_schema:
            response_schema = create_swagger_type_from_dict(f'{name}SqlRequestSchema', response_schema)
        sql_endpoint_class = create_sql_endpoint_class(
            name,
            method,
            url,
            sql,
            self.repository,
            query_parameters,
            tags,
            request_schema,
            response_schema,
            description,
        )
        api.add_resource(sql_endpoint_class, sql_endpoint_class.route,
                         endpoint=sql_endpoint_class.endpoint)

    def get_table_endpont_creation_args(self, action, columns_map, endpoint, model_name, request_fields_excluded,
                                        response_fields_excluded, table_id_field, table_name, table_extensions):
        _endpoint_args = {}
        if endpoint == 'GET':
            if 'LIST' == action:
                _endpoint_args = {
                    'model_name': model_name,
                    'table_name': table_name,
                    'columns_map': columns_map,
                    'request_fields_excluded': request_fields_excluded,
                    'table_id_field': table_id_field,
                    'table_extensions': table_extensions,
                }
            if 'SINGLE' == action:
                _endpoint_args = {
                    'model_name': model_name,
                    'table_name': table_name,
                    'columns_map': columns_map,
                    'request_fields_excluded': request_fields_excluded,
                    'table_id_field': table_id_field,
                    'table_extensions': table_extensions,
                }
        if endpoint == 'PUT':
            if 'LIST' == action:
                _endpoint_args = {
                    'model_name': model_name,
                    'table_name': table_name,
                    'columns_map': columns_map,
                    'table_id_field': table_id_field,
                    'request_fields_excluded': request_fields_excluded,
                    'table_extensions': table_extensions,
                }
            if 'SINGLE' == action:
                _endpoint_args = {
                    'model_name': model_name,
                    'table_name': table_name,
                    'columns_map': columns_map,
                    'table_id_field': table_id_field,
                    'request_fields_excluded': request_fields_excluded,
                    'response_fields_excluded': response_fields_excluded,
                    'table_extensions': table_extensions,
                }
        if endpoint == 'POST':
            if 'LIST' == action:
                _endpoint_args = {
                    'model_name': model_name,
                    'table_name': table_name,
                    'columns_map': columns_map,
                    'table_id_field': table_id_field,
                    'request_fields_excluded': request_fields_excluded,
                    'table_extensions': table_extensions,
                }
            if 'SINGLE' == action:
                _endpoint_args = {
                    'model_name': model_name,
                    'table_name': table_name,
                    'columns_map': columns_map,
                    'request_fields_excluded': request_fields_excluded,
                    'response_fields_excluded': response_fields_excluded,
                    'table_id_field': table_id_field,
                    'table_extensions': table_extensions,
                }
        if endpoint == 'DELETE':
            if 'LIST' == action:
                _endpoint_args = {
                    'model_name': model_name,
                    'table_name': table_name,
                    'columns_map': columns_map,
                    'table_id_field': table_id_field,
                    'table_extensions': table_extensions,
                }
            if 'SINGLE' == action:
                _endpoint_args = {
                    'model_name': model_name,
                    'table_name': table_name,
                    'columns_map': columns_map,
                    'request_fields_excluded': request_fields_excluded,
                    'table_id_field': table_id_field,
                    'table_extensions': table_extensions,
                }
        return _endpoint_args

    def get_fields_excluded(self, action, columns_names, endpoint, table, table_default_fields_excluded):
        request_table_field_default_excluded_endpoint_action = []
        request_default_fields_excluded = []
        if endpoint in self.fields_excluded and action in self.fields_excluded[endpoint]:
            request_table_field_default_excluded_endpoint_action = self.fields_excluded[endpoint][action].copy()
            request_default_fields_excluded = request_table_field_default_excluded_endpoint_action.copy()

        if 'fields_excluded' in table and endpoint in table['fields_excluded'] and action in \
                table['fields_excluded'][endpoint]:
            request_table_field_default_excluded_endpoint_action.extend(
                x for x in table['fields_excluded'][endpoint][action] if
                x not in request_default_fields_excluded)

        request_table_field_default_excluded_endpoint_action = [c for c in
                                                                request_table_field_default_excluded_endpoint_action if
                                                                c in columns_names]
        fields_excluded = table_default_fields_excluded.copy()
        fields_excluded.extend(
            x for x in request_table_field_default_excluded_endpoint_action if
            x not in table_default_fields_excluded)

        return fields_excluded

    def get_form(self, class_name: str, columns_map: dict, method: str, as_array=False):
        form_class = create_form_class(class_name, method, columns_map)
        form_schema_json = generate_form_swagger_schema_from_form(method, form_class, as_array=as_array)

        return form_class, form_schema_json

    def remove_id_field_from_allowed_columns(self, allowed_columns, columns_map, id_field):
        if id_field in columns_map.keys():
            del (columns_map[id_field])
            allowed_columns.remove(id_field)

    def get_id_field_where_name_and_swagger_type(self, columns_map, id_field):
        # get the real field to lookup the id requested
        id_field_where = id_field if id_field is not None else "id"
        # get the type of the lookup field
        id_field_where_type = f'{columns_map[id_field_where].pytype.__name__}:'
        if id_field_where_type != 'int:':
            id_field_where_type = ''
        return id_field_where, id_field_where_type

    def get_class_name_from_model_name(self, model_name):
        class_name = model_name.replace("_", " ").title().replace(" ", "")
        return class_name

    def parse_columns(self, columns_map: dict, table_fields_excluded: List):
        # filter allowed columns
        allowed_columns = [c for c in columns_map.keys() if c not in table_fields_excluded]
        map = columns_map.copy()
        if len(allowed_columns) > 0:
            map = columns_map_filter_allowed_columns(columns_map, allowed_columns)

        return allowed_columns, map

    def set_id_field_if_none(self, id_field):
        if id_field is None:
            id_field = 'id'
        return id_field

    def create_get_single_endpoint(
            self,
            model_name: str,
            table_name: str,
            columns_map: map,
            request_fields_excluded: List,
            table_id_field: str,
            table_extensions: dict,
    ):
        class_name = self.get_class_name_from_model_name(model_name)
        allowed_columns, columns_map = self.parse_columns(columns_map, request_fields_excluded)
        id_field_where, id_field_where_type = self.get_id_field_where_name_and_swagger_type(columns_map, table_id_field)

        return create_get_single_endpoint_class(
            table_name,
            model_name,
            id_field_where_type,
            class_name,
            id_field_where,
            allowed_columns,
            self.repository,
            columns_map,
            table_extensions
        )

    def create_put_single_endpoint(
            self,
            model_name: str,
            table_name: str,
            columns_map: map,
            table_id_field: map,
            request_fields_excluded: List,
            response_fields_excluded: List,
            table_extensions: dict,
    ):
        class_name = self.get_class_name_from_model_name(model_name)
        request_allowed_columns, request_columns_map = self.parse_columns(
            columns_map,
            request_fields_excluded)
        response_allowed_columns, response_columns_map = self.parse_columns(
            columns_map,
            response_fields_excluded)
        form_class, form_schema_model = self.get_form(class_name, request_columns_map, 'put')
        id_field_where, id_field_where_type = self.get_id_field_where_name_and_swagger_type(columns_map, table_id_field)

        return create_put_single_endpoint_class(
            table_name,
            model_name,
            form_class,
            class_name,
            form_schema_model,
            request_allowed_columns,
            self.repository,
            response_columns_map,
            id_field_where,
            table_extensions
        )

    def create_post_single_endpoint(
            self,
            model_name: str,
            table_name: str,
            columns_map: map,
            request_fields_excluded: List,
            response_fields_excluded: List,
            table_id_field: str,
            table_extensions: dict,
    ):
        class_name = self.get_class_name_from_model_name(model_name)
        request_allowed_columns, request_columns_map = self.parse_columns(columns_map, request_fields_excluded)
        response_allowed_columns, response_columns_map = self.parse_columns(columns_map, response_fields_excluded)
        form_class, form_schema_model = self.get_form(class_name, request_columns_map, 'post')
        id_field_where, id_field_where_type = self.get_id_field_where_name_and_swagger_type(columns_map, table_id_field)

        return create_post_single_endpoint_class(
            table_name,
            model_name,
            form_class,
            table_id_field,
            class_name,
            form_schema_model,
            request_allowed_columns,
            self.repository,
            response_columns_map,
            id_field_where,
            id_field_where_type,
            table_extensions
        )

    def create_delete_single_endpoint(
            self,
            model_name: str,
            table_name: str,
            columns_map: map,
            request_fields_excluded: List,
            table_id_field: str,
            table_extensions: dict,
    ):
        class_name = self.get_class_name_from_model_name(model_name)
        table_id_field = self.set_id_field_if_none(table_id_field)
        allowed_columns, columns_map = self.parse_columns(columns_map, request_fields_excluded)
        id_field_where, id_field_where_type = self.get_id_field_where_name_and_swagger_type(columns_map, table_id_field)

        return create_delete_single_endpoint_class(
            table_name,
            model_name,
            class_name,
            allowed_columns,
            self.repository,
            id_field_where,
            id_field_where_type,
            table_extensions
        )

    def create_get_list_endpoint(
            self,
            model_name: str,
            table_name: str,
            columns_map: map,
            request_fields_excluded: List,
            table_id_field: str,
            table_extensions: dict,
    ):
        class_name = self.get_class_name_from_model_name(model_name)
        allowed_columns, columns_map = self.parse_columns(columns_map, request_fields_excluded)
        id_field_where, id_field_where_type = self.get_id_field_where_name_and_swagger_type(columns_map, table_id_field)

        return create_get_list_endpoint_class(
            table_name,
            model_name,
            class_name,
            id_field_where,
            allowed_columns,
            self.repository,
            columns_map,
            table_extensions
        )

    def create_put_list_endpoint(
            self,
            model_name: str,
            table_name: str,
            columns_map: map,
            table_id_field: str,
            request_fields_excluded: List,
            table_extensions: dict,
    ):
        class_name = self.get_class_name_from_model_name(model_name)
        request_allowed_columns, request_columns_map = self.parse_columns(
            columns_map,
            request_fields_excluded
        )
        form_class, form_schema_model = self.get_form(class_name, request_columns_map, 'put_list_item', as_array=True)

        id_field_where, id_field_where_type = self.get_id_field_where_name_and_swagger_type(columns_map, table_id_field)

        return create_put_list_endpoint_class(
            table_name,
            model_name,
            form_class,
            class_name,
            form_schema_model,
            request_allowed_columns,
            self.repository,
            id_field_where,
            table_extensions
        )

    def create_post_list_endpoint(
            self,
            model_name: str,
            table_name: str,
            columns_map: map,
            table_id_field: str,
            request_fields_excluded: List,
            table_extensions: dict,
    ):
        class_name = self.get_class_name_from_model_name(model_name)
        request_allowed_columns, request_columns_map = self.parse_columns(
            columns_map,
            request_fields_excluded
        )

        form_class, form_schema_model = self.get_form(class_name, request_columns_map, 'post_list_item', as_array=True)
        id_field_where, id_field_where_type = self.get_id_field_where_name_and_swagger_type(columns_map, table_id_field)

        return create_post_list_endpoint_class(
            table_name,
            model_name,
            form_class,
            class_name,
            form_schema_model,
            self.repository,
            id_field_where,
            table_extensions
        )

    def create_delete_list_endpoint(
            self,
            model_name: str,
            table_name: str,
            columns_map: map,
            table_id_field: str,
            table_extensions: dict,
    ):
        class_name = self.get_class_name_from_model_name(model_name)
        id_field_where, id_field_where_type = self.get_id_field_where_name_and_swagger_type(columns_map, table_id_field)

        return create_delete_list_endpoint_class(
            table_name,
            model_name,
            class_name,
            self.repository,
            table_id_field,
            id_field_where_type,
            table_extensions
        )
