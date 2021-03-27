from flask import request, jsonify, make_response
from flask_restful_swagger_3 import swagger, Schema as SwaggerSchema, Resource

from src.application.api_generator import getResponseModel, getRequestModel, getEntitySchema
from src.application.api_generator.form import getFormClass, generate_form_schema_from_form, get_filtering, \
    get_filtered_response, FilterModel, OrderByModel

from src.db import db


def get_list_response_model(entity, class_name=None):
    class ListResponseModel(SwaggerSchema):
        type = 'object'
        properties = {
            'page': {
                'type': 'integer',
                'format': 'int64',
            },
            'per_page': {
                'type': 'integer',
                'format': 'int64',
            },
            'items': {
                'type': 'array',
                'items': [
                    {
                        'type': 'object',
                        'schema': getResponseModel(entity, class_name)
                    }
                ]
            },
            'filters': {
                'type': 'array',
                'items': [
                    {
                        'type': 'object',
                        'schema': FilterModel
                    }
                ]
            },
            'order_by': {
                'type': 'array',
                'items': [
                    {
                        'type': 'object',
                        'schema': OrderByModel
                    }
                ]
            }
        }

    ListResponseModel.__name__ = f'{class_name}ListResponseModel'

    return ListResponseModel


def get_form_new_resource(entity, api_schema, class_name=None, form_custom_properties=None):
    class FormNewResource(Resource):
        @swagger.doc({
            'tags': [class_name],
            'description': f'Get a form model for {class_name}',
            'responses': {
                '200': {
                    'description': f'Form {class_name} response model'
                }
            }
        })
        def get(self):
            formClass = getFormClass(entity, class_name, form_custom_properties)
            return make_response(jsonify(generate_form_schema_from_form(formClass)), 200)

        @swagger.doc({
            'tags': [class_name],
            'description': f'Submit endpoint {class_name}',
            'responses': {
                '200': {
                    'description': f'{class_name} response model',
                    'content': {
                        'application/json': {
                            'schema': getResponseModel(entity, class_name)
                        }
                    }
                }
            }
        })
        def put(self):
            formClass = getFormClass(entity, class_name, form_custom_properties)
            form = formClass(request.form)
            if not form.validate():
                return make_response(jsonify(form.errors), 400)

            form_data = form.data
            created = entity(**{k: v for k, v in form_data.items()})  # with **obj breaks ? lol

            db.session.add(created)
            db.session.commit()
            return make_response(api_schema.dump(created), 200)

    FormNewResource.__name__ = f'{class_name}FormNewResource'

    return FormNewResource


def get_update_form_api_resource(entity, api_schema, class_name=None, form_custom_properties=None):
    class FormUpdateResource(Resource):
        @swagger.doc({
            'tags': [class_name],
            'description': f'Get a form model for {class_name}',
            'parameters': [
                {
                    'name': 'id',
                    'description': f'{class_name} identifier',
                    'in': 'path',
                    'schema': {
                        'type': 'integer'
                    }
                }
            ],
            'responses': {
                '200': {
                    'description': f'Form {class_name} response model'
                }
            }
        })
        def get(self, id):
            object = entity.query.get(id)

            if object == None:
                return None, 404

            formClass = getFormClass(entity, class_name, form_custom_properties)
            form = formClass(obj=object)
            return make_response(jsonify(generate_form_schema_from_form(form, object)), 200)

        @swagger.doc({
            'tags': [class_name],
            'description': f'Submit endpoint for {class_name}',
            'parameters': [
                {
                    'name': 'id',
                    'description': f'{class_name} identifier',
                    'in': 'path',
                    'schema': {
                        'type': 'integer'
                    }
                }
            ],
            'responses': {
                '200': {
                    'description': f'{class_name} response model',
                    'content': {
                        'application/json': {
                            'schema': getResponseModel(entity, class_name)
                        }
                    }
                }
            }
        })
        def post(self, id):
            object = entity.query.get(id)

            if object == None:
                return None, 404

            formClass = getFormClass(entity, class_name, form_custom_properties)
            form = formClass(request.form)

            if not form.validate():
                return jsonify(form.errors), 400

            form.populate_obj(object)
            db.session.commit()

            return api_schema.dump(object)

    FormUpdateResource.__name__ = f'{class_name}FormUpdateResource'

    return FormUpdateResource


def get_client_list_api_resource(entity, api_schema_multi, class_name=None):
    class ListResource(Resource):
        @swagger.doc({
            'tags': [class_name],
            'description': f'Get a {class_name}',
            'parameters': [
                {
                    'name': 'page',
                    'description': 'page number',
                    'in': 'query',
                    'schema': {
                        'type': 'integer'
                    }
                },
                {
                    'name': 'per_page',
                    'description': 'Number of items per page',
                    'in': 'query',
                    'schema': {
                        'type': 'integer'
                    }
                },
                {
                    'name': 'filters',
                    'description': 'Filters array',
                    'in': 'query',
                    'schema': {
                        'type': 'array',
                        'items': [{
                            'type': 'string',
                            'description': 'FilterModel JSON',
                            'example': '{"field": "name", "op": "==", "value": ["test"]}'
                        }]
                    }
                },
                {
                    'name': 'order_by',
                    'description': 'Order by array',
                    'in': 'query',
                    'schema': {
                        'type': 'array',
                        'items': [{
                            'type': 'string',
                            'description': 'OrderByModel JSON',
                            'example': '{"field": "name","direction":"desc"}'
                        }]
                    }
                }
            ],
            'responses': {
                '200': {
                    'description': f'{class_name} response model',
                    'content': {
                        'application/json': {
                            'schema': get_list_response_model(entity, class_name)
                        }
                    }
                }
            }
        })
        def get(self):
            query = entity.query
            filters, page, per_page, order_by = get_filtering(request.args)
            response = get_filtered_response(filters, order_by, page, per_page, query, api_schema_multi)
            return make_response(jsonify(response), 200)

    ListResource.__name__ = f'{class_name}ListResource'

    return ListResource


def get_create_api_resource(entity, api_schema, class_name=None, required_fields=None):
    class CreateResource(Resource):
        @swagger.doc({
            'tags': [class_name],
            'description': f'Create a {class_name}',
            'requestBody': {
                'description': f'{class_name} request model',
                'required': True,
                'content': {
                    'application/json': {
                        'schema': getRequestModel(entity, class_name, required_fields),
                        'examples': {
                            'application/json': {
                                'name': 'somebody'
                            }
                        }
                    }
                }
            },
            'responses': {
                '200': {
                    'description': 'Client response model',
                    'content': {
                        'application/json': {
                            'schema': getResponseModel(entity, class_name),
                        }
                    }
                }
            }
        })
        def put(self):
            form_class = getFormClass(entity, class_name)
            form = form_class()
            form.from_json(api_schema.dump(request.json))

            if not form.validate():
                return make_response(jsonify(form.errors), 400)

            form_data = form.data
            created = entity(**{k: v for k, v in form_data.items()})  # with **obj breaks ? lol

            db.session.add(created)
            db.session.commit()
            return make_response(api_schema.dump(created), 200)

    CreateResource.__name__ = f'{class_name}CreateResource'

    return CreateResource


def get_single_operations_resource(entity, api_schema, class_name=None, required_fields=None):
    class SingleOperationsResource(Resource):
        @swagger.doc({
            'tags': [class_name],
            'description': f'Update a {class_name}',
            'parameters': [
                {
                    'name': 'id',
                    'description': f'{class_name} identifier',
                    'in': 'path',
                    'schema': {
                        'type': 'integer'
                    }
                }
            ],
            'requestBody': {
                'description': f'{class_name} request model',
                'required': True,
                'content': {
                    'application/json': {
                        'schema': getRequestModel(entity, class_name, required_fields)
                    }
                }
            },
            'responses': {
                '200': {
                    'description': 'Client response model',
                    'content': {
                        'application/json': {
                            'schema': getResponseModel(entity, class_name)
                        }
                    }
                }
            }
        })
        def post(self, id):
            object = entity.query.get(id)

            if object == None:
                return None, 404

            formClass = getFormClass(entity, class_name)
            form = formClass(obj=object)
            form.from_json(api_schema.dump(request.json))

            if not form.validate():
                return make_response(jsonify(form.errors), 400)

            form.populate_obj(object)
            db.session.commit()

            return make_response(api_schema.dump(object))

        @swagger.doc({
            'tags': [class_name],
            'description': f'Get a {class_name}',
            'parameters': [
                {
                    'name': 'id',
                    'description': f'{class_name} identifier',
                    'in': 'path',
                    'schema': {
                        'type': 'integer'
                    }
                }
            ],
            'responses': {
                '200': {
                    'description': f'{class_name} response model',
                    'content': {
                        'application/json': {
                            'schema': getResponseModel(entity, class_name)
                        }
                    }
                }
            }
        })
        def get(self, id):
            object = entity.query.get(id)

            if object == None:
                return None, 404

            return make_response(api_schema.dump(object), 200)

        @swagger.doc({
            'tags': [class_name],
            'description': f'Delete a {class_name}',
            'parameters': [
                {
                    'name': 'id',
                    'description': f'{class_name} identifier',
                    'in': 'path',
                    'schema': {
                        'type': 'integer'
                    }
                }
            ],
            'responses': {
                '200': {
                    'description': f'{class_name} deleted',
                }
            }
        })
        def delete(self, id):
            object = db.session.query(entity).get(id)

            if object == None:
                return None, 404

            db.session.delete(object)
            db.session.commit()
            return make_response(jsonify({'message': f'{class_name} deleted'}))

    SingleOperationsResource.__name__ = f'{class_name}SingleOperationsResource'

    return SingleOperationsResource


def register_api_resources(api, resources={}):
    for route, resource in resources.items():
        api.add_resource(resource, route)


def buildApiResources(api, entity, class_name, route_name, required_fields=None, form_custom_properties=None):
    EntitySchema = getEntitySchema(entity, class_name)
    api_schema = EntitySchema()
    api_schema_multi = EntitySchema(many=True)  # lists
    FormNewResource = get_form_new_resource(entity, api_schema, class_name, form_custom_properties)
    FormUpdateResource = get_update_form_api_resource(entity, api_schema, class_name, form_custom_properties)
    ListResource = get_client_list_api_resource(entity, api_schema_multi, class_name)
    CreateResource = get_create_api_resource(entity, api_schema, class_name, required_fields)
    SingleOperationsResource = get_single_operations_resource(entity, api_schema, class_name, required_fields)
    register_api_resources(api, {
        f'/{route_name}/form': FormNewResource,
        f'/{route_name}/form/<int:id>': FormUpdateResource,
        f'/{route_name}/list': ListResource,
        f'/{route_name}/': CreateResource,
        f'/{route_name}/<int:id>': SingleOperationsResource,
    })


def build(api, entity, class_name, route_name, required_fields=None, form_custom_properties=None):
    buildApiResources(api, entity, class_name, route_name, required_fields, form_custom_properties)
