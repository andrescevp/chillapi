from datetime import datetime
from typing import List

import psycopg2
import simplejson
import sqlalchemy
from flask import request
from flask_restful_swagger_3 import swagger, Schema as SwaggerSchema
from wtforms.validators import ValidationError
import inflect
from openapi_schema_validator import validate as json_swagger_schema_validator
from jsonschema.exceptions import ValidationError as JsonSchemaValidationError
from simplejson.errors import JSONDecodeError

from chillapi.extensions.audit import AuditLog
from chillapi.database import DB_DIALECT_POSTGRES
from chillapi.database.repository import DataRepository, _MAGIC_QUERIES
from chillapi.exceptions.api_manager import ConfigError
from chillapi.exceptions.http import NotFoundException, RequestSchemaError
from chillapi.logger.app_loggers import logger
from chillapi.database.query_builder import create_select_filtered_paginated_ordered_query, create_select_filtered_paginated_query_count, \
    create_select_join_soft_delete_filter
from chillapi.swagger.http import AutomaticResource, ResourceResponse
from chillapi.swagger.schemas import get_get_single_endpoint_schema, get_put_single_endpoint_schema, \
    get_post_single_endpoint_schema, get_delete_single_endpoint_schema, get_get_list_endpoint_schema, \
    get_put_list_endpoint_schema, get_post_list_endpoint_schema, get_delete_list_endpoint_schema, \
    create_swagger_type_from_dict
from chillapi.swagger.utils import get_response_swagger_schema, \
    get_revisable_response_swagger_schema, get_error_swagger_schema, get_not_found_swagger_schema, \
    get_list_filtered_response_swagger_schema, get_list_filtered_request_swagger_schema, get_filter_schema, \
    get_order_schema, get_size_schema

revisable_response_swagger_schema = get_revisable_response_swagger_schema()
error_swagger_schema = get_error_swagger_schema()
not_found_swagger_schema = get_not_found_swagger_schema()

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


def create_get_single_endpoint_class(
        table_name: str,
        model_name: str,
        id_field_where_type: str,
        class_name: str,
        id_field_where: str,
        allowed_columns: List,
        repository: DataRepository,
        columns_map: dict,
        table_extensions: dict,
):
    response_schema = get_response_swagger_schema(columns_map, f'{class_name}GetSingleEndpoint')
    soft_delete_enabled, soft_delete_field = _get_extension_default_field(table_extensions, 'soft_delete')

    class GetSingleEndpoint(AutomaticResource):
        route = f'/read/{model_name}/<{id_field_where_type}id>'
        endpoint = f'/{model_name}GetSingleEndpoint'

        def request(self, **args) -> ResourceResponse:
            id = args['id']
            try:
                response = ResourceResponse()

                query = {f'{id_field_where}': {'op': '=', 'value': id}}
                query_values = {f'{id_field_where}': id}

                if soft_delete_enabled:
                    query = {**query, **{f'{soft_delete_field}': {'op': 'isnull', 'value': None}}}
                    query_values = {**query_values, **{f'{soft_delete_field}': None}}

                record = repository.fetch_by(
                    table_name,
                    allowed_columns,
                    query,
                    query_values,
                )

                response.response = record.one()._asdict()
            except sqlalchemy.exc.NoResultFound:
                raise NotFoundException(description=f'{class_name} with id: {id} not found')

            response.audit = AuditLog(f'Read {table_name} record', action='READ',
                                      current_status=response.response,
                                      change_parameters={'entity': class_name, 'record_id': id})
            return response

        @swagger.doc(get_get_single_endpoint_schema(class_name, id_field_where_type, response_schema))
        def get(self, id):
            return self.process_request(id=id)

    GetSingleEndpoint.__name__ = GetSingleEndpoint.endpoint
    return GetSingleEndpoint


def create_put_single_endpoint_class(
        table_name: str,
        model_name: str,
        form_class: classmethod,
        class_name: str,
        form_schema_model: type(SwaggerSchema),
        request_allowed_columns: List,
        repository: DataRepository,
        response_columns_map: dict,
        id_field: str,
        table_extensions: dict
):
    response_schema = get_response_swagger_schema(response_columns_map, f'{class_name}PutSingleEndpoint')
    request_schema = get_put_single_endpoint_schema(class_name, form_schema_model, response_schema)
    extension = 'on_create_timestamp'
    extension_enabled, extension_field = _get_extension_default_field(table_extensions, extension)

    class PutSingleEndpoint(AutomaticResource):
        route = f'/create/{model_name}'
        endpoint = f'{model_name}PutSingleEndpoint'

        def validate_request(self, **args):
            form = args['form']
            if not form.validate():
                raise ValidationError(message=simplejson.dumps(form.errors))

        def request(self, **args) -> ResourceResponse:
            form = args['form']
            form_data = form.data
            response = ResourceResponse()
            try:

                params = form_data
                columns = request_allowed_columns
                if extension_field and extension_field not in columns:
                    columns += [extension_field]
                if extension_field and extension_field not in params:
                    params[extension_field] = datetime.now().isoformat()

                result = repository.insert_record(table_name, columns, params,
                                                  returning_field=id_field)
                form_data[id_field] = result

                if extension_field and extension_field not in request_allowed_columns:
                    del (form_data[extension_field])

                response.response = form_data

                response.audit = AuditLog(f'Create {table_name} record', action='CREATE',
                                          current_status=response.response,
                                          change_parameters={**{'entity': class_name}, **params})

            except sqlalchemy.exc.IntegrityError as e:
                if isinstance(e.orig, psycopg2.errors.UniqueViolation):
                    raise ValidationError(message=e.orig)
                if isinstance(e.orig, psycopg2.errors.ForeignKeyViolation):
                    raise ValidationError(message=e.orig)

            return response

        @swagger.doc(request_schema)
        def put(self):
            data = request.json
            form = form_class(data=data)
            return self.process_request(form=form)

    PutSingleEndpoint.__name__ = PutSingleEndpoint.endpoint

    return PutSingleEndpoint


def create_post_single_endpoint_class(
        table_name: str,
        model_name: str,
        form_class: classmethod,
        id_field: str,
        class_name: str,
        form_schema_model: type(SwaggerSchema),
        request_allowed_columns: List,
        repository: DataRepository,
        columns_map: dict,
        id_field_where: str,
        id_field_where_type: str,
        table_extensions: dict
):
    response_schema = get_response_swagger_schema(columns_map, f'{class_name}PostSingleEndpoint')
    request_schema = get_post_single_endpoint_schema(class_name, form_schema_model,
                                                     response_schema, id_field_where_type)

    update_extension_enabled, update_field = _get_extension_default_field(table_extensions, 'on_update_timestamp')
    soft_delete_extension_enabled, soft_delete_field = _get_extension_default_field(table_extensions, 'soft_delete')

    class PostSingleEndpoint(AutomaticResource):
        route = f'/update/{model_name}/<{id_field_where_type}id>'
        endpoint = f'/{model_name}PostSingleEndpoint'

        def request(self, **args) -> ResourceResponse:
            form = args['form']
            form_data = form.data
            oid = args['id']
            response = ResourceResponse()

            try:
                if update_extension_enabled and update_field not in form_data:
                    form_data[update_field] = datetime.now().isoformat()

                repository.update_record(
                    table_name,
                    id_field_where,
                    oid,
                    {**form_data, **{id_field_where: oid}}
                )

                if update_extension_enabled and update_field in form_data:
                    del (form_data[update_field])
                response.response = form_data

            except sqlalchemy.exc.IntegrityError as e:
                if isinstance(e.orig, psycopg2.errors.UniqueViolation):
                    raise ValidationError(message=e.orig)
                if isinstance(e.orig, psycopg2.errors.ForeignKeyViolation):
                    raise ValidationError(message=e.orig)

            response.audit = AuditLog(f'Update {table_name} record', action='UPDATE',
                                      current_status=response.response,
                                      prev_status=args['validation_output'],
                                      change_parameters={**{'entity': class_name, f'{id_field}': oid}, **form_data})

            return response

        def validate_request(self, **args):
            form = args['form']
            id = args['id']
            try:
                logger.debug('Check entity exists',
                             extra=args)

                query = {f'{id_field_where}': {'op': '=', 'value': id}}
                query_values = {f'{id_field_where}': id}

                if soft_delete_extension_enabled:
                    query = {**query, **{f'{soft_delete_field}': {'op': 'isnull', 'value': None}}}
                    query_values = {**query_values, **{f'{soft_delete_field}': None}}

                record = repository.fetch_by(
                    table_name,
                    ['*'],
                    query,
                    query_values
                )

                if not form.validate():
                    raise ValidationError(message=simplejson.dumps(form.errors))

                return record.one()._asdict()
            except sqlalchemy.exc.NoResultFound:
                raise NotFoundException(description=f'{class_name} with id: {id} not found')
            except JsonSchemaValidationError:
                raise RequestSchemaError()

        @swagger.doc(request_schema)
        def post(self, id):
            data = request.json
            form = form_class(data=data)
            return self.process_request(form=form, id=id)

    PostSingleEndpoint.__name__ = PostSingleEndpoint.endpoint

    return PostSingleEndpoint


def create_delete_single_endpoint_class(
        table_name: str,
        model_name: str,
        class_name: str,
        allowed_columns: List,
        repository: DataRepository,
        id_field_where: str,
        id_field_where_type: str,
        table_extensions: dict
):
    extension = 'soft_delete'
    extension_enabled, extension_field = _get_extension_default_field(table_extensions, extension)

    class DeleteSingleEndpoint(AutomaticResource):
        route = f'/delete/{model_name}/<{id_field_where_type}id>'
        endpoint = f'/{model_name}DeleteSingleEndpoint'

        def request(self, **args) -> ResourceResponse:
            id = args['id']
            response = ResourceResponse()
            response.response = {
                'code': 500,
                'message': 'error',
                'errors': []
            }

            try:
                now = datetime.now().isoformat()
                if extension_enabled:
                    repository.update_record(
                        table_name,
                        id_field_where,
                        id,
                        {id_field_where: id, extension_field: now}
                    )
                    response.response['message'] = 'ok'
                    response.response['code'] = 200

                    if 'cascade' in table_extensions[extension]:
                        _cascades = table_extensions[extension]['cascade']
                        if 'one_to_many' in _cascades:
                            _one_to_many = _cascades['one_to_many']
                            for _otm, _relation in enumerate(_one_to_many):
                                _relation_table = _relation['table']
                                _pk = _relation['column_id']
                                _fk = _relation['column_fk']
                                _relation_ids = repository.fetch_by(
                                    _relation_table,
                                    [_pk],
                                    {_fk: {'op': '=', 'value': id}},
                                    {_fk: id}
                                )
                                _cascade_ids = [x[0] for x in _relation_ids.fetchall()]
                                soft_deletes_one_to_many = [{extension_field: now, _pk: x} for x in _cascade_ids]
                                repository.update_batch(_relation_table, soft_deletes_one_to_many, where_field=_pk)
                        if 'many_to_many' in _cascades:
                            _one_to_many = _cascades['many_to_many']
                            for _otm, _relation in enumerate(_one_to_many):
                                _relation_table = _relation['table']
                                _relation_join_table = _relation['join_table']
                                _pk = _relation['column_id']
                                _relation_columns = _relation['join_columns']
                                _relation_column_id = _relation['column_id']
                                sql = create_select_join_soft_delete_filter(_relation_table, _relation_column_id,
                                                                            _relation_join_table, _relation_columns)
                                _relation_ids = repository.execute(sql, {'id': id})
                                _cascade_ids = [x[0] for x in _relation_ids.fetchall()]
                                soft_deletes_one_to_many = [{extension_field: now, _pk: x} for x in _cascade_ids]
                                repository.update_batch(_relation_table, soft_deletes_one_to_many, where_field=_pk)

                    response.audit = AuditLog(f'Delete {table_name} record', action='SOFT DELETE',
                                              current_status={'deleted': 'deleted'},
                                              prev_status=args['validation_output'],
                                              change_parameters={'entity': class_name, 'id': id})
                else:
                    repository.delete_record(table_name, id_field_where, id)
                    response.response['message'] = 'ok'
                    response.response['code'] = 200

                    response.audit = AuditLog(f'Delete {table_name} record', action='DELETE',
                                              current_status={'deleted': 'deleted'},
                                              prev_status=args['validation_output'],
                                              change_parameters={'entity': class_name, 'id': id})

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
                             extra=args)
                query = {f'{id_field_where}': {'op': '=', 'value': oid}}
                query_values = {f'{id_field_where}': oid}
                if extension_enabled:
                    query = {**query, **{f'{extension_field}': {'op': 'isnull', 'value': None}}}
                    query_values = {**query_values, **{f'{extension_field}': None}}

                record = repository.fetch_by(
                    table_name,
                    ['*'],
                    query,
                    query_values
                )

                return record.one()._asdict()
            except sqlalchemy.exc.NoResultFound:
                raise NotFoundException(description=f'{class_name} with id: {oid} not found')

        @swagger.doc(get_delete_single_endpoint_schema(class_name, id_field_where_type))
        def delete(self, id):
            return self.process_request(id=id)

    DeleteSingleEndpoint.__name__ = DeleteSingleEndpoint.endpoint

    return DeleteSingleEndpoint


def create_get_list_endpoint_class(
        table_name: str,
        model_name: str,
        class_name: str,
        id_field_where: str,
        allowed_columns: List,
        repository: DataRepository,
        columns_map: dict,
        table_extensions: dict
):
    request_schema_query_filters = get_list_filtered_request_swagger_schema(class_name, columns_map)
    response_schema_query_filters = get_list_filtered_request_swagger_schema(class_name, columns_map)
    response_schema = get_list_filtered_response_swagger_schema(columns_map, response_schema_query_filters,
                                                                f'{class_name}GetListEndpoint')
    swagger_schema = get_get_list_endpoint_schema(class_name, response_schema, request_schema_query_filters)
    filter_schema = get_filter_schema(class_name).definitions()
    order_schema = get_order_schema(class_name).definitions()
    size_schema = get_size_schema(class_name).definitions()

    soft_delete_enabled, soft_delete_field = _get_extension_default_field(table_extensions, 'soft_delete')

    class GetListEndpoint(AutomaticResource):
        route = f'/read/{inflector.plural(model_name)}'
        endpoint = f'/{model_name}GetListEndpoint'

        def validate_request(self, **args):
            query = {}
            errors = {}
            schema = filter_schema
            for parameter_name in columns_map.keys():
                self.validate_query_parameter(errors, parameter_name, query, schema)

            parameter_name = 'order'
            schema = order_schema
            self.validate_query_parameter(errors, parameter_name, query, schema, default={
                'field': [id_field_where],
                'direction': 'asc'
            })

            parameter_name = 'size'
            schema = size_schema
            self.validate_query_parameter(errors, parameter_name, query, schema, default={
                'limit': 100,
                'offset': 0
            })

            if len(errors.keys()) > 0:
                raise ValidationError(errors)

            return query

        def validate_query_parameter(self, errors, parameter_name, query, schema, default=None):
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
            if soft_delete_enabled:
                query[soft_delete_field] = {'op': 'isnull', 'value': None}
            query_no_limit = query.copy()
            del (query_no_limit['size'])
            query_no_limit_params = {k: v['value'] for k, v in query_no_limit.items() if 'op' in v}
            count_sql = create_select_filtered_paginated_query_count(table_name, query_no_limit, id_field_where)

            count_record = repository.execute(count_sql, query_no_limit_params)
            count = count_record.one()._asdict().get('count')

            response = ResourceResponse()
            data = {}

            if count > 0:
                query_params = {k: v['value'] for k, v in query.items() if 'op' in v}
                sql = create_select_filtered_paginated_ordered_query(table_name, allowed_columns, query)
                record = repository.execute(sql, query_params)
                data = record.fetchall()

            if soft_delete_enabled:
                del query[soft_delete_field]

            response.response = {
                'data': data,
                '_meta': {**query, **{'total_records': count}}
            }

            if count == 0:
                response.http_code = 404

            response.audit = AuditLog(f'Read List {table_name} record', action='READ',
                                      current_status={'deleted': 'deleted'},
                                      prev_status=args['validation_output'],
                                      change_parameters={'entity': class_name})

            return response

        @swagger.doc(swagger_schema)
        def get(self):
            return self.process_request()

    GetListEndpoint.__name__ = GetListEndpoint.endpoint
    return GetListEndpoint


def create_put_list_endpoint_class(
        table_name: str,
        model_name: str,
        form_class: classmethod,
        class_name: str,
        form_schema_model: type(SwaggerSchema),
        request_allowed_columns: List,
        repository: DataRepository,
        id_field: str,
        table_extensions: dict
):
    request_schema = get_put_list_endpoint_schema(class_name, form_schema_model)
    extension = 'on_create_timestamp'
    extension_enabled, extension_field = _get_extension_default_field(table_extensions, extension)
    columns = request_allowed_columns
    if extension_enabled:
        columns += [extension_field]

    class PutListEndpoint(AutomaticResource):
        route = f'/create/{inflector.plural(model_name)}'
        endpoint = f'{model_name}PutListEndpoint'

        def validate_request(self, **args):
            if len(args['data']) > form_schema_model.maxItems:
                raise ValidationError(message=f'Body too large, max items: {form_schema_model.maxItems}')
            if len(args['data']) < form_schema_model.minItems:
                raise ValidationError(message=f'Body too small, min items: {form_schema_model.minItems}')
            forms = args['form']
            errors = {}
            for i, form in enumerate(forms):
                if not form.validate():
                    errors[i] = form.errors

            if len(errors.keys()) > 0:
                raise ValidationError(message=simplejson.dumps(errors))

        def request(self, **args) -> ResourceResponse:
            forms = args['form']
            form_data = []
            for form in forms:
                _form_data = form.data
                if extension_enabled:
                    _form_data[extension_field] = datetime.now().isoformat()
                form_data.append(_form_data)
            # form_data = [form.data for form in forms]
            response = ResourceResponse()
            response.response = {
                'message': 'error',
                'details': []
            }

            try:

                result = repository.insert_batch(table_name, columns, form_data,
                                                 returning_field=id_field)
                response.response['message'] = f'Affected rows: {result}'
                response.response['code'] = 200
                response.http_code = 200
            except sqlalchemy.exc.IntegrityError as e:
                if isinstance(e.orig, psycopg2.errors.UniqueViolation):
                    raise ValidationError(message=e.orig)
                if isinstance(e.orig, psycopg2.errors.ForeignKeyViolation):
                    raise ValidationError(message=e.orig)

            return response

        @swagger.doc(request_schema)
        def put(self):
            data = request.json
            form = [form_class(data=item) for item in data]
            return self.process_request(form=form, data=data)

    PutListEndpoint.__name__ = PutListEndpoint.endpoint

    return PutListEndpoint


def create_post_list_endpoint_class(
        table_name: str,
        model_name: str,
        form_class: classmethod,
        class_name: str,
        form_schema_model: type(SwaggerSchema),
        repository: DataRepository,
        id_field: str,
        table_extensions: dict
):
    request_schema = get_post_list_endpoint_schema(class_name, form_schema_model)
    extension = 'on_update_timestamp'
    extension_enabled, extension_field = _get_extension_default_field(table_extensions, extension)

    class PostListEndpoint(AutomaticResource):
        route = f'/update/{inflector.plural(model_name)}'
        endpoint = f'{model_name}PostListEndpoint'

        def validate_request(self, **args):
            forms = args['form']
            if len(args['data']) > form_schema_model.maxItems:
                raise ValidationError(message=f'Body too large, max items: {form_schema_model.maxItems}')
            if len(args['data']) < form_schema_model.minItems:
                raise ValidationError(message=f'Body too small, min items: {form_schema_model.minItems}')

            errors = {}
            ids = []
            for i, form in enumerate(forms):
                _data = form.data
                ids.append(_data[id_field])
                if not form.validate():
                    errors[i] = form.errors

            ids_check_sql = _MAGIC_QUERIES[DB_DIALECT_POSTGRES]['get_ids_not_in_table_from_list']({
                'values': [f':{id}' for id in ids],
                'id_field': id_field,
                'table': table_name,
                'where': f'WHERE {extension_field} IS NULL' if extension_enabled else '',
            })

            ids_check = repository.execute(ids_check_sql, {str(id): id for id in ids})
            not_found = ids_check.fetchall()
            if len(not_found) > 0:
                errors = {**errors, **{str(x[0]): 'id not found' for x in not_found}}

            if len(errors.keys()) > 0:
                raise ValidationError(message=simplejson.dumps(errors))

        def request(self, **args) -> ResourceResponse:
            forms = args['form']
            form_data = []
            for form in forms:
                _form_data = form.data
                if extension_enabled:
                    _form_data[extension_field] = datetime.now().isoformat()
                form_data.append(_form_data)
            response = ResourceResponse()
            try:
                repository.update_batch(table_name, form_data, where_field=id_field)
                response.response = form_data
            except sqlalchemy.exc.IntegrityError as e:
                if isinstance(e.orig, psycopg2.errors.UniqueViolation):
                    raise ValidationError(message=e.orig)
                if isinstance(e.orig, psycopg2.errors.ForeignKeyViolation):
                    raise ValidationError(message=e.orig)

            return response

        @swagger.doc(request_schema)
        def post(self):
            data = request.json
            form = [form_class(data=item) for item in data]
            return self.process_request(form=form, data=data)

    PostListEndpoint.__name__ = PostListEndpoint.endpoint

    return PostListEndpoint


def create_delete_list_endpoint_class(
        table_name: str,
        model_name: str,
        class_name: str,
        repository: DataRepository,
        id_field: str,
        id_field_where_type: str,
        table_extensions: dict
):
    id_field_swagger_type = 'string'
    if id_field_where_type == 'int:':
        id_field_swagger_type = 'integer'
    request_body_schema = create_swagger_type_from_dict(f'{class_name}DeleteListRequestSchema', {
        'type': 'array',
        'description': 'Id list',
        'items': {'type': id_field_swagger_type}
    })
    request_schema = get_delete_list_endpoint_schema(class_name, request_body_schema)
    extension = 'soft_delete'
    extension_enabled, extension_field = _get_extension_default_field(table_extensions, extension)

    class DeleteListEndpoint(AutomaticResource):
        route = f'/delete/{inflector.plural(model_name)}'
        endpoint = f'{model_name}DeleteListEndpoint'

        def validate_request(self, **args):
            ids = args['data']
            errors = {}
            try:
                json_swagger_schema_validator(ids, request_body_schema.definitions())
            except JsonSchemaValidationError as e:
                raise ValidationError(message=e)

            ids_check_sql = _MAGIC_QUERIES[DB_DIALECT_POSTGRES]['get_ids_not_in_table_from_list']({
                'values': [f':{id}' for id in ids],
                'id_field': id_field,
                'table': table_name,
                'where': f'WHERE {extension_field} IS NULL' if extension_enabled else '',
            })

            ids_check = repository.execute(ids_check_sql, {str(id): id for id in ids})
            not_found = ids_check.fetchall()
            if len(not_found) > 0:
                errors = {str(x[0]): 'id not found' for x in not_found}
            if len(errors.keys()) > 0:
                raise ValidationError(message=simplejson.dumps(errors))

        def request(self, **args) -> ResourceResponse:
            data = args['data']

            response = ResourceResponse()
            try:
                if extension_enabled:
                    now = datetime.now().isoformat()
                    soft_deletes = [{extension_field: now, id_field: x} for x in data]
                    repository.update_batch(table_name, soft_deletes, where_field=id_field)

                    if 'cascade' in table_extensions[extension]:
                        _cascades = table_extensions[extension]['cascade']
                        if 'one_to_many' in _cascades:
                            _one_to_many = _cascades['one_to_many']
                            for _otm, _relation in enumerate(_one_to_many):
                                _relation_table = _relation['table']
                                _pk = _relation['column_id']
                                _fk = _relation['column_fk']
                                _cascade_ids = []
                                for _fk_id in data:
                                    _relation_ids = repository.fetch_by(
                                        _relation_table,
                                        [_pk],
                                        {_fk: {'op': '=', 'value': _fk_id}},
                                        {_fk: _fk_id}
                                    )
                                    _cascade_ids += [x[0] for x in _relation_ids.fetchall()]
                                soft_deletes_one_to_many = [{extension_field: now, _pk: x} for x in _cascade_ids]
                                repository.update_batch(_relation_table, soft_deletes_one_to_many, where_field=_pk)
                        if 'many_to_many' in _cascades:
                            _one_to_many = _cascades['many_to_many']
                            for _otm, _relation in enumerate(_one_to_many):
                                _relation_table = _relation['table']
                                _relation_join_table = _relation['join_table']
                                _pk = _relation['column_id']
                                _relation_columns = _relation['join_columns']
                                _relation_column_id = _relation['column_id']
                                _cascade_ids = []
                                for _fk_id in data:
                                    sql = create_select_join_soft_delete_filter(_relation_table, _relation_column_id,
                                                                                _relation_join_table, _relation_columns)
                                    _relation_ids = repository.execute(sql, {'id': _fk_id})
                                    _cascade_ids += [x[0] for x in _relation_ids.fetchall()]
                                soft_deletes_one_to_many = [{extension_field: now, _pk: x} for x in _cascade_ids]
                                repository.update_batch(_relation_table, soft_deletes_one_to_many, where_field=_pk)
                else:
                    repository.delete_batch(table_name, data)
                response.response = 'ok'
            except sqlalchemy.exc.IntegrityError as e:
                if isinstance(e.orig, psycopg2.errors.UniqueViolation):
                    raise ValidationError(message=e.orig)
                if isinstance(e.orig, psycopg2.errors.ForeignKeyViolation):
                    raise ValidationError(message=e.orig)

            return response

        @swagger.doc(request_schema)
        def delete(self):
            data = request.json
            return self.process_request(data=data)

    DeleteListEndpoint.__name__ = DeleteListEndpoint.endpoint

    return DeleteListEndpoint
