from typing import List

import inflect
import psycopg2
import simplejson
import sqlalchemy
from flask import request
from jsonschema.exceptions import ValidationError as JsonSchemaValidationError
from openapi_schema_validator import validate as json_swagger_schema_validator
from simplejson.errors import JSONDecodeError
from wtforms.validators import ValidationError

from chillapi.abc import Repository
from chillapi.app.flask_restful_swagger_3 import swagger
from chillapi.app.forms import create_form_class, generate_form_swagger_schema_from_form
from chillapi.database import DB_DIALECT_POSTGRES
from chillapi.database.query_builder import (
    create_select_filtered_paginated_ordered_query,
    create_select_filtered_paginated_query_count,
    )
from chillapi.database.repository import _MAGIC_QUERIES
from chillapi.exceptions.api_manager import ConfigError
from chillapi.exceptions.http import NotFoundException, RequestSchemaError
from chillapi.extensions.audit import AuditLog
from chillapi.logger.app_loggers import logger
from chillapi.swagger.http import AutomaticResource, ResourceResponse
from chillapi.swagger.schemas import (
    create_swagger_type_from_dict, get_delete_list_endpoint_schema, get_delete_single_endpoint_schema, get_get_list_endpoint_schema,
    get_get_single_endpoint_schema, get_post_list_endpoint_schema, get_post_single_endpoint_schema, get_put_list_endpoint_schema,
    get_put_single_endpoint_schema,
    )
from chillapi.swagger.utils import (
    get_error_swagger_schema, get_filter_schema, get_list_filtered_request_swagger_schema, get_list_filtered_response_swagger_schema,
    get_not_found_swagger_schema, get_order_schema, get_response_swagger_schema, get_revisable_response_swagger_schema, get_size_schema,
    python_to_swagger_types,
    )

revisable_response = get_revisable_response_swagger_schema()
error_response = get_error_swagger_schema()
not_found = get_not_found_swagger_schema()

inflector = inflect.engine()


def _get_extension_default_field(table_extensions, extension):
    _registered = extension in table_extensions.keys()
    _enable = False
    default_field = None
    if 'enable' in table_extensions[extension]:
        _enable = table_extensions[extension]['enable']
    if _registered and _enable:
        default_field = table_extensions[extension]['default_field']
    if _enable and default_field is None:
        raise ConfigError(f'{extension} is enabled but there is not default_field')

    return _enable, default_field


def _get_form(class_name: str, columns_map: dict, method: str, as_array = False):
    form_class = create_form_class(class_name, method, columns_map)
    form_schema_json = generate_form_swagger_schema_from_form(method, form_class, as_array = as_array)

    return form_class, form_schema_json


def _column_type_to_swagger_type_url(type):
    id_field_where_type = f'{type.python_type.__name__}:'
    if id_field_where_type != 'int:':
        id_field_where_type = ''
    return id_field_where_type


def create_get_single_endpoint_class(
        table: dict,
        allowed_columns: List,
        allowed_columns_map: dict,
        extensions: dict,
        repository: Repository
        ):
    table_slug = table['slug']
    table_name = table['name']
    model_name = table['model_name']
    id_field = table['id_field']

    id_field_where_type = _column_type_to_swagger_type_url(table['columns'][id_field]['type'])
    response_schema = get_response_swagger_schema(allowed_columns_map, f'{model_name}GetSingleEndpoint')
    soft_delete_extension = extensions['soft_delete']
    swagger_docs = get_get_single_endpoint_schema(model_name, id_field_where_type, response_schema)

    class GetSingleEndpoint(AutomaticResource):
        route = f'/read/{table_slug}/<{id_field_where_type}id>'
        endpoint = f'/{model_name}GetSingleEndpoint'
        representations = swagger_docs

        def request(self, **args) -> ResourceResponse:
            id = args['id']
            try:
                response = ResourceResponse()

                query = {id_field: {'op': '=', 'value': id}}
                query_values = {id_field: id}

                if soft_delete_extension.enabled:
                    query, query_values, soft_delete_extension.add_query_filter(query, query_values)

                record = repository.fetch_by(
                        table_name,
                        allowed_columns,
                        query,
                        query_values,
                        )

                response.response = record.one()._asdict()
            except sqlalchemy.exc.NoResultFound:
                raise NotFoundException(description = f'{model_name} with id: {id} not found')

            response.audit = AuditLog(f'Read {table_name} record', action = 'READ',
                                      current_status = response.response,
                                      change_parameters = {'entity': model_name, 'record_id': id})
            return response

        @swagger.doc(swagger_docs)
        def get(self, id):
            return self.process_request(id = id)

    GetSingleEndpoint.__name__ = GetSingleEndpoint.endpoint
    return GetSingleEndpoint


def create_put_single_endpoint_class(
        table: dict,
        allowed_columns: List,
        allowed_columns_map: dict,
        extensions: dict,
        repository: Repository
        ):
    table_slug = table['slug']
    table_name = table['name']
    model_name = table['model_name']
    id_field = table['id_field']
    response_schema = get_response_swagger_schema(allowed_columns_map, f'{model_name}PutSingleEndpoint')
    extension = extensions['on_create_timestamp']
    extension_enabled = extension.enabled
    form_class, form_schema_model = _get_form(table['model_name'], allowed_columns_map, 'put')
    request_schema = get_put_single_endpoint_schema(model_name, form_schema_model, response_schema)

    class PutSingleEndpoint(AutomaticResource):
        route = f'/create/{table_slug}'
        endpoint = f'{model_name}PutSingleEndpoint'
        representations = request_schema

        def validate_request(self, **args):
            form = args['form']
            if not form.validate():
                raise ValidationError(message = simplejson.dumps(form.errors))

        def request(self, **args) -> ResourceResponse:
            form = args['form']
            form_data = form.data
            response = ResourceResponse()
            try:

                params = form_data
                columns = allowed_columns

                if extension_enabled:
                    columns = extension.set_columns(columns)
                if extension_enabled:
                    params = extension.set_field_data(params)

                result = repository.insert_record(table_name, columns, params,
                                                  returning_field = id_field)
                form_data[id_field] = result

                if extension_enabled:
                    params = extension.unset_field_data(params)

                response.response = form_data

                response.audit = AuditLog(f'Create {table_name} record', action = 'CREATE',
                                          current_status = response.response,
                                          change_parameters = {**{'entity': model_name}, **params})

            except sqlalchemy.exc.IntegrityError as e:
                if isinstance(e.orig, psycopg2.errors.UniqueViolation):
                    raise ValidationError(message = e.orig)
                if isinstance(e.orig, psycopg2.errors.ForeignKeyViolation):
                    raise ValidationError(message = e.orig)

            return response

        @swagger.doc(request_schema)
        def put(self):
            data = request.json
            form = form_class(data = data)
            return self.process_request(form = form)

    PutSingleEndpoint.__name__ = PutSingleEndpoint.endpoint

    return PutSingleEndpoint


def create_post_single_endpoint_class(
        table: dict,
        allowed_columns: List,
        allowed_columns_map: dict,
        extensions: dict,
        repository: Repository
        ):
    table_slug = table['slug']
    table_name = table['name']
    model_name = table['model_name']
    id_field = table['id_field']

    response_schema = get_response_swagger_schema(allowed_columns_map, f'{model_name}PostSingleEndpoint')
    update_extension = extensions['on_update_timestamp']
    soft_delete_extension = extensions['soft_delete']

    form_class, form_schema_model = _get_form(table['model_name'], allowed_columns_map, 'post')

    id_field_where_type = _column_type_to_swagger_type_url(table['columns'][id_field]['type'])
    request_schema = get_post_single_endpoint_schema(model_name, form_schema_model, response_schema,
                                                     id_field_where_type)

    class PostSingleEndpoint(AutomaticResource):
        route = f'/update/{table_slug}/<{id_field_where_type}id>'
        endpoint = f'/{model_name}PostSingleEndpoint'
        representations = request_schema

        def request(self, **args) -> ResourceResponse:
            form = args['form']
            form_data = form.data
            oid = args['id']
            response = ResourceResponse()

            try:
                if update_extension.enabled:
                    form_data = update_extension.set_field_data(form_data)

                repository.update_record(
                        table_name,
                        id_field,
                        oid,
                        {**form_data, **{id_field: oid}}
                        )

                if update_extension.enabled:
                    form_data = update_extension.unset_field_data(form_data)
                response.response = form_data

            except sqlalchemy.exc.IntegrityError as e:
                if isinstance(e.orig, psycopg2.errors.UniqueViolation):
                    raise ValidationError(message = e.orig)
                if isinstance(e.orig, psycopg2.errors.ForeignKeyViolation):
                    raise ValidationError(message = e.orig)

            response.audit = AuditLog(f'Update {table_name} record', action = 'UPDATE',
                                      current_status = response.response,
                                      prev_status = args['validation_output'],
                                      change_parameters = {**{'entity': model_name, f'{id_field}': oid}, **form_data})

            return response

        def validate_request(self, **args):
            form = args['form']
            id = args['id']
            try:
                logger.debug('Check entity exists',
                             extra = args)

                query = {f'{id_field}': {'op': '=', 'value': id}}
                query_values = {f'{id_field}': id}

                if soft_delete_extension.enabled:
                    query, query_values = soft_delete_extension.add_query_filter(query, query_values)

                record = repository.fetch_by(
                        table_name,
                        ['*'],
                        query,
                        query_values
                        )

                if not form.validate():
                    raise ValidationError(message = simplejson.dumps(form.errors))

                return record.one()._asdict()
            except sqlalchemy.exc.NoResultFound:
                raise NotFoundException(description = f'{model_name} with id: {id} not found')
            except JsonSchemaValidationError:
                raise RequestSchemaError()

        @swagger.doc(request_schema)
        def post(self, id):
            data = request.json
            form = form_class(data = data)
            return self.process_request(form = form, id = id)

    PostSingleEndpoint.__name__ = PostSingleEndpoint.endpoint

    return PostSingleEndpoint


def create_delete_single_endpoint_class(
        table: dict,
        allowed_columns: List,
        allowed_columns_map: dict,
        extensions: dict,
        repository: Repository
        ):
    table_slug = table['slug']
    table_name = table['name']
    model_name = table['model_name']
    id_field = table['id_field']

    id_field_where_type = _column_type_to_swagger_type_url(table['columns'][id_field]['type'])

    soft_delete_extension = extensions['soft_delete']
    request_schema = get_delete_single_endpoint_schema(model_name, id_field_where_type)

    class DeleteSingleEndpoint(AutomaticResource):
        route = f'/delete/{table_slug}/<{id_field_where_type}id>'
        endpoint = f'/{model_name}DeleteSingleEndpoint'
        representations = request_schema

        def request(self, **args) -> ResourceResponse:
            id = args['id']
            response = ResourceResponse()
            response.response = {
                    'code':    500,
                    'message': 'error',
                    'errors':  []
                    }

            try:
                if soft_delete_extension.enabled:
                    response = soft_delete_extension.soft_delete(id_field, id, response)

                    response.audit = AuditLog(f'Delete {table_name} record', action = 'SOFT DELETE',
                                              current_status = {'deleted': 'deleted'},
                                              prev_status = args['validation_output'],
                                              change_parameters = {'entity': model_name, 'id': id})
                else:
                    repository.delete_record(table_name, id_field, id)
                    response.response['message'] = 'ok'
                    response.response['code'] = 200

                    response.audit = AuditLog(f'Delete {table_name} record', action = 'DELETE',
                                              current_status = {'deleted': 'deleted'},
                                              prev_status = args['validation_output'],
                                              change_parameters = {'entity': model_name, 'id': id})

            except sqlalchemy.exc.IntegrityError as e:
                if isinstance(e.orig, psycopg2.errors.ForeignKeyViolation):
                    response.response['errors'].append(f'ForeignKeyViolation : {e.orig}')
                    response.response['code'] = 400
                else:
                    response.response['errors'].append(f'IntegrityError : {e.orig}')
                    response.response['code'] = 500

            response.http_code = response.response['code']

            return response

        def validate_request(self, **args):
            oid = args['id']
            try:
                logger.debug('Check entity exists',
                             extra = args)
                query = {f'{id_field}': {'op': '=', 'value': oid}}
                query_values = {f'{id_field}': oid}

                if soft_delete_extension.enabled:
                    query, query_values, soft_delete_extension.add_query_filter(query, query_values)

                record = repository.fetch_by(
                        table_name,
                        ['*'],
                        query,
                        query_values
                        )

                return record.one()._asdict()
            except sqlalchemy.exc.NoResultFound:
                raise NotFoundException(description = f'{model_name} with id: {oid} not found')

        @swagger.doc(request_schema)
        def delete(self, id):
            return self.process_request(id = id)

    DeleteSingleEndpoint.__name__ = DeleteSingleEndpoint.endpoint

    return DeleteSingleEndpoint


def create_get_list_endpoint_class(
        table: dict,
        allowed_columns: List,
        allowed_columns_map: dict,
        extensions: dict,
        repository: Repository
        ):
    table_slug = table['slug']
    table_name = table['name']
    model_name = table['model_name']
    id_field = table['id_field']

    request_schema_query_filters = get_list_filtered_request_swagger_schema(model_name, allowed_columns_map)
    response_schema_query_filters = get_list_filtered_request_swagger_schema(model_name, allowed_columns_map)
    response_schema = get_list_filtered_response_swagger_schema(allowed_columns_map, response_schema_query_filters,
                                                                f'{model_name}GetListEndpoint')
    swagger_schema = get_get_list_endpoint_schema(model_name, response_schema, request_schema_query_filters)
    filter_schema = get_filter_schema(model_name).definitions()
    order_schema = get_order_schema(model_name).definitions()
    size_schema = get_size_schema(model_name).definitions()
    soft_delete_extension = extensions['soft_delete']

    class GetListEndpoint(AutomaticResource):
        route = f'/read/{inflector.plural(table_slug)}'
        endpoint = f'/{model_name}GetListEndpoint'
        representations = swagger_schema

        def validate_request(self, **args):
            query = {}
            errors = {}
            schema = filter_schema
            for parameter_name in allowed_columns_map.keys():
                self.validate_query_parameter(errors, parameter_name, query, schema)

            parameter_name = 'order'
            schema = order_schema
            self.validate_query_parameter(errors, parameter_name, query, schema, default = {
                    'field':     [id_field],
                    'direction': 'asc'
                    })

            parameter_name = 'size'
            schema = size_schema
            self.validate_query_parameter(errors, parameter_name, query, schema, default = {
                    'limit':  100,
                    'offset': 0
                    })

            if len(errors.keys()) > 0:
                raise ValidationError(errors)

            return query

        def validate_query_parameter(self, errors, parameter_name, query, schema, default = None):
            try:
                value = request.args.get(parameter_name)
                if value is not None:
                    json_value = simplejson.loads(value)
                    json_swagger_schema_validator(json_value, schema)
                    query[parameter_name] = json_value

                if value is None and default is not None:
                    json_swagger_schema_validator(default, schema)
                    query[parameter_name] = default
            except JsonSchemaValidationError as e:
                error_msg = e.message.replace('\n', ' ')
                if parameter_name not in errors.keys():
                    errors[parameter_name] = []
                errors[parameter_name].append(f"'{parameter_name}' query parameter is not valid: {error_msg}")
            except JSONDecodeError as e:
                if parameter_name not in errors.keys():
                    errors[parameter_name] = []
                errors[parameter_name].append(
                        f"'{parameter_name}' query parameter seem to be a malformed JSON: {e.msg}")
            except Exception:
                if parameter_name not in errors.keys():
                    errors[parameter_name] = []
                errors[parameter_name].append(f"'{parameter_name}' query parameter seem to be a malformed JSON")

        def request(self, **args) -> ResourceResponse:
            query = args['validation_output']
            if soft_delete_extension.enabled:
                query, _qv = soft_delete_extension.add_query_filter(query, {})
            query_no_limit = query.copy()
            del (query_no_limit['size'])
            query_no_limit_params = {k: v['value'] for k, v in query_no_limit.items() if 'op' in v}
            count_sql = create_select_filtered_paginated_query_count(table_name, query_no_limit, id_field)

            count_record = repository.execute(count_sql, query_no_limit_params)
            count = count_record.one()._asdict().get('count')

            response = ResourceResponse()
            data = {}

            if count > 0:
                query_params = {k: v['value'] for k, v in query.items() if 'op' in v}
                sql = create_select_filtered_paginated_ordered_query(table_name, allowed_columns, query)
                record = repository.execute(sql, query_params)
                data = record.fetchall()

            if soft_delete_extension.enabled:
                query = soft_delete_extension.unset_field_data(query)

            response.response = {
                    'data':  data,
                    '_meta': {**query, **{'total_records': count}}
                    }

            if count == 0:
                response.http_code = 404

            response.audit = AuditLog(f'Read List {table_name} record', action = 'READ',
                                      current_status = {'deleted': 'deleted'},
                                      prev_status = args['validation_output'],
                                      change_parameters = {'entity': model_name})

            return response

        @swagger.doc(swagger_schema)
        def get(self):
            return self.process_request()

    GetListEndpoint.__name__ = GetListEndpoint.endpoint
    return GetListEndpoint


def create_put_list_endpoint_class(
        table: dict,
        allowed_columns: List,
        allowed_columns_map: dict,
        extensions: dict,
        repository: Repository
        ):
    table_slug = table['slug']
    table_name = table['name']
    model_name = table['model_name']
    id_field = table['id_field']

    create_extension = extensions['on_create_timestamp']

    form_class, form_schema_model = _get_form(table['model_name'], allowed_columns_map, 'putList')

    request_schema = get_put_list_endpoint_schema(model_name, form_schema_model)

    columns = allowed_columns
    if create_extension.enabled:
        columns += [create_extension.config['default_field']]

    class PutListEndpoint(AutomaticResource):
        route = f'/create/{inflector.plural(table_slug)}'
        endpoint = f'{model_name}PutListEndpoint'
        representations = request_schema

        def validate_request(self, **args):
            if len(args['data']) > form_schema_model.maxItems:
                raise ValidationError(message = f'Body too large, max items: {form_schema_model.maxItems}')
            if len(args['data']) < form_schema_model.minItems:
                raise ValidationError(message = f'Body too small, min items: {form_schema_model.minItems}')
            forms = args['form']
            errors = {}
            for i, form in enumerate(forms):
                if not form.validate():
                    errors[i] = form.errors

            if len(errors.keys()) > 0:
                raise ValidationError(message = simplejson.dumps(errors))

        def request(self, **args) -> ResourceResponse:
            forms = args['form']
            form_data = []
            for form in forms:
                _form_data = form.data
                if create_extension.enabled:
                    _form_data = create_extension.set_field_data(_form_data)
                form_data.append(_form_data)
            # form_data = [form.data for form in forms]
            response = ResourceResponse()
            response.response = {
                    'message': 'error',
                    'details': []
                    }

            try:

                result = repository.insert_batch(table_name, columns, form_data,
                                                 returning_field = id_field)
                response.response['message'] = f'Affected rows: {result}'
                response.response['code'] = 200
                response.http_code = 200
            except sqlalchemy.exc.IntegrityError as e:
                if isinstance(e.orig, psycopg2.errors.UniqueViolation):
                    raise ValidationError(message = e.orig)
                if isinstance(e.orig, psycopg2.errors.ForeignKeyViolation):
                    raise ValidationError(message = e.orig)

            return response

        @swagger.doc(request_schema)
        def put(self):
            data = request.json
            form = [form_class(data = item) for item in data]
            return self.process_request(form = form, data = data)

    PutListEndpoint.__name__ = PutListEndpoint.endpoint

    return PutListEndpoint


def create_post_list_endpoint_class(
        table: dict,
        allowed_columns: List,
        allowed_columns_map: dict,
        extensions: dict,
        repository: Repository
        ):
    table_slug = table['slug']
    table_name = table['name']
    model_name = table['model_name']
    id_field = table['id_field']
    form_class, form_schema_model = _get_form(model_name, allowed_columns_map, 'postList')

    request_schema = get_post_list_endpoint_schema(model_name, form_schema_model)
    extension = extensions['on_update_timestamp']

    class PostListEndpoint(AutomaticResource):
        route = f'/update/{inflector.plural(table_slug)}'
        endpoint = f'{model_name}PostListEndpoint'
        representations = request_schema

        def validate_request(self, **args):
            forms = args['form']
            if len(args['data']) > form_schema_model.maxItems:
                raise ValidationError(message = f'Body too large, max items: {form_schema_model.maxItems}')
            if len(args['data']) < form_schema_model.minItems:
                raise ValidationError(message = f'Body too small, min items: {form_schema_model.minItems}')

            errors = {}
            ids = []
            for i, form in enumerate(forms):
                _data = form.data
                ids.append(_data[id_field])
                if not form.validate():
                    errors[i] = form.errors

            ids_check_sql = _MAGIC_QUERIES[DB_DIALECT_POSTGRES]['get_ids_not_in_table_from_list']({
                    'values':   [f':{id}' for id in ids],
                    'id_field': id_field,
                    'table':    table_name,
                    'where':    f'WHERE {extension.config["default_field"]} IS NULL' if extension.enabled else '',
                    })

            ids_check = repository.execute(ids_check_sql, {str(id): id for id in ids})
            not_found = ids_check.fetchall()
            if len(not_found) > 0:
                errors = {**errors, **{str(x[0]): 'id not found' for x in not_found}}

            if len(errors.keys()) > 0:
                raise ValidationError(message = simplejson.dumps(errors))

        def request(self, **args) -> ResourceResponse:
            forms = args['form']
            form_data = []
            for form in forms:
                _form_data = form.data
                if extension.enabled:
                    _form_data = extension.set_field_data(_form_data)

                form_data.append(_form_data)
            response = ResourceResponse()
            try:
                repository.update_batch(table_name, form_data, where_field = id_field)
                response.response = form_data
            except sqlalchemy.exc.IntegrityError as e:
                if isinstance(e.orig, psycopg2.errors.UniqueViolation):
                    raise ValidationError(message = e.orig)
                if isinstance(e.orig, psycopg2.errors.ForeignKeyViolation):
                    raise ValidationError(message = e.orig)

            return response

        @swagger.doc(request_schema)
        def post(self):
            data = request.json
            form = [form_class(data = item) for item in data]
            return self.process_request(form = form, data = data)

    PostListEndpoint.__name__ = PostListEndpoint.endpoint

    return PostListEndpoint


def create_delete_list_endpoint_class(
        table: dict,
        allowed_columns: List,
        allowed_columns_map: dict,
        extensions: dict,
        repository: Repository
        ):
    table_slug = table['slug']
    table_name = table['name']
    model_name = table['model_name']
    id_field = table['id_field']

    id_field_where_type = python_to_swagger_types(table['columns'][id_field]['type'].python_type.__name__)

    request_body_schema = create_swagger_type_from_dict(f'{model_name}DeleteListRequestSchema', {
            'type':        'array',
            'description': 'Id list',
            'items':       {'type': id_field_where_type}
            })
    request_schema = get_delete_list_endpoint_schema(model_name, request_body_schema)

    extension = extensions['soft_delete']

    class DeleteListEndpoint(AutomaticResource):
        route = f'/delete/{inflector.plural(table_slug)}'
        endpoint = f'{model_name}DeleteListEndpoint'
        representations = request_schema

        def validate_request(self, **args):
            ids = args['data']
            errors = {}
            try:
                json_swagger_schema_validator(ids, request_body_schema.definitions())
            except JsonSchemaValidationError as e:
                raise ValidationError(message = e)

            ids_check_sql = _MAGIC_QUERIES[DB_DIALECT_POSTGRES]['get_ids_not_in_table_from_list']({
                    'values':   [f':{id}' for id in ids],
                    'id_field': id_field,
                    'table':    table_name,
                    'where':    f'WHERE {extension.config["default_field"]} IS NULL' if extension.enabled else '',
                    })

            ids_check = repository.execute(ids_check_sql, {str(id): id for id in ids})
            not_found = ids_check.fetchall()
            if len(not_found) > 0:
                errors = {str(x[0]): 'id not found' for x in not_found}
            if len(errors.keys()) > 0:
                raise ValidationError(message = simplejson.dumps(errors))

        def request(self, **args) -> ResourceResponse:
            data = args['data']

            response = ResourceResponse()
            try:
                if extension.enabled:
                    extension.soft_delete_batch(table_name, extension.config['default_field'], id_field, data)
                else:
                    repository.delete_batch(table_name, data)
                response.response = 'ok'
            except sqlalchemy.exc.IntegrityError as e:
                if isinstance(e.orig, psycopg2.errors.UniqueViolation):
                    raise ValidationError(message = e.orig)
                if isinstance(e.orig, psycopg2.errors.ForeignKeyViolation):
                    raise ValidationError(message = e.orig)

            return response

        @swagger.doc(request_schema)
        def delete(self):
            data = request.json
            return self.process_request(data = data)

    DeleteListEndpoint.__name__ = DeleteListEndpoint.endpoint

    return DeleteListEndpoint
