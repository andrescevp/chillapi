from flask_restful_swagger_3 import Schema as SwaggerSchema
from marshmallow_sqlalchemy import ModelSchema
from src.application.api_generator.form import generate_swagger_properties

from src.application.api_generator.crud_endpoints import get_form_new_resource, get_update_form_api_resource, \
    get_client_list_api_resource, get_create_api_resource, get_single_operations_resource, buildApiResources


def getRequestModel(entity, class_name=None, required_fields=None):
    class RequestModel(SwaggerSchema):
        type = 'object'
        properties = generate_swagger_properties(entity, True)
        required = required_fields

    RequestModel.__name__ = f'{class_name}RequestModel'

    return RequestModel


def getResponseModel(entity, class_name=None):
    class ResponseModel(SwaggerSchema):
        type = 'object'
        properties = generate_swagger_properties(entity)

    ResponseModel.__name__ = f'{class_name}ResponseModel'

    return ResponseModel


def getEntitySchema(entity, class_name=None):
    class Schema(ModelSchema):
        class Meta:
            model = entity

    Schema.__name__ = f'{class_name}Schema'

    return Schema


def register_api_resources(api, resources: dict = dict({})):
    for route, resource in resources.items():
        api.add_resource(resource, route)


def build_api_endpoint(api, entity, class_name, route_name, required_fields=None, form_custom_properties=None):
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
