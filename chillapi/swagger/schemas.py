from typing import List

from ..app.swagger_schema import Schema
from ..swagger.utils import get_error_swagger_schema, get_not_found_swagger_schema, get_revisable_response_swagger_schema

revisable_response_swagger_schema = get_revisable_response_swagger_schema()
error_swagger_schema = get_error_swagger_schema()
not_found_swagger_schema = get_not_found_swagger_schema()


def create_swagger_type_from_dict(name, swagger_dict_definition):
    """

    :param name:
    :param swagger_dict_definition:

    """
    return type(name, (Schema,), swagger_dict_definition)


def get_get_single_endpoint_schema(class_name, id_field_where_type, response_schema):
    """

    :param class_name:
    :param id_field_where_type:
    :param response_schema:

    """
    return {
        "tags": [class_name],
        "description": f"Get a {class_name} model representation",
        "parameters": [
            {
                "name": "id",
                "description": f"{class_name} identifier",
                "in": "path",
                "schema": {"type": "integer" if id_field_where_type == "int:" else "string"},
            }
        ],
        "responses": {
            "200": {"description": f"{class_name} response model", "content": {"application/json": {"schema": response_schema}}},
            "404": {"description": "Not found response model", "content": {"application/json": {"schema": not_found_swagger_schema}}},
            "500": {"description": "Operation fail", "content": {"application/json": {"schema": error_swagger_schema}}},
        },
    }


def get_put_single_endpoint_schema(class_name, form_schema_model, response_schema):
    """

    :param class_name:
    :param form_schema_model:
    :param response_schema:

    """
    return {
        "tags": [class_name],
        "description": f"Create a {class_name}",
        "requestBody": {
            "description": f"{class_name} request model",
            "required": True,
            "content": {"application/json": {"schema": form_schema_model}},
        },
        "responses": {
            "200": {"description": f"{class_name} response model", "content": {"application/json": {"schema": response_schema}}},
            "500": {"description": "Operation fail", "content": {"application/json": {"schema": error_swagger_schema}}},
        },
    }


def get_post_single_endpoint_schema(class_name, form_schema_model, response_schema, id_field_where_type):
    """

    :param class_name:
    :param form_schema_model:
    :param response_schema:
    :param id_field_where_type:

    """
    return {
        "tags": [class_name],
        "description": f"Update a {class_name}",
        "parameters": [
            {
                "name": "id",
                "description": f"{class_name} identifier",
                "in": "path",
                "schema": {"type": "integer" if id_field_where_type == "int:" else "string"},
            }
        ],
        "requestBody": {
            "description": f"{class_name} request model",
            "required": True,
            "content": {"application/json": {"schema": form_schema_model}},
        },
        "responses": {
            "200": {"description": f"{class_name} response model", "content": {"application/json": {"schema": response_schema}}},
            "404": {"description": "Not found response model", "content": {"application/json": {"schema": not_found_swagger_schema}}},
            "500": {"description": "Operation fail", "content": {"application/json": {"schema": error_swagger_schema}}},
        },
    }


def get_delete_single_endpoint_schema(class_name, id_field_where_type):
    """

    :param class_name:
    :param id_field_where_type:

    """
    return {
        "tags": [class_name],
        "description": f"Update a {class_name}",
        "parameters": [
            {
                "name": "id",
                "description": f"{class_name} identifier",
                "in": "path",
                "schema": {"type": "integer" if id_field_where_type == "int:" else "string"},
            }
        ],
        "responses": {
            "200": {"description": "Operation success", "content": {"application/json": {"schema": revisable_response_swagger_schema}}},
            "400": {"description": "Operation fail", "content": {"application/json": {"schema": error_swagger_schema}}},
            "404": {"description": "Not found response model", "content": {"application/json": {"schema": not_found_swagger_schema}}},
            "500": {"description": "Operation fail", "content": {"application/json": {"schema": error_swagger_schema}}},
        },
    }


def get_get_list_endpoint_schema(class_name, response_schema, request_schema):
    """

    :param class_name:
    :param response_schema:
    :param request_schema:

    """
    return {
        "tags": [class_name],
        "description": f"Get {class_name} model list",
        "parameters": request_schema,
        "responses": {
            "200": {"description": f"{class_name} list response model", "content": {"application/json": {"schema": response_schema}}},
            "404": {"description": "Not found response model", "content": {"application/json": {"schema": not_found_swagger_schema}}},
            "500": {"description": "Operation fail", "content": {"application/json": {"schema": error_swagger_schema}}},
        },
    }


def get_put_list_endpoint_schema(class_name, form_schema_model):
    """

    :param class_name:
    :param form_schema_model:

    """
    return {
        "tags": [class_name],
        "description": f"Create several {class_name}",
        "requestBody": {
            "description": f"{class_name} request model",
            "required": True,
            "content": {"application/json": {"schema": form_schema_model}},
        },
        "responses": {
            "200": {"description": f"{class_name} response model", "content": {"application/json": {"schema": revisable_response_swagger_schema}}},
            "400": {"description": "Operation fail", "content": {"application/json": {"schema": error_swagger_schema}}},
            "500": {"description": "Operation fail", "content": {"application/json": {"schema": error_swagger_schema}}},
        },
    }


def get_post_list_endpoint_schema(class_name, form_schema_model):
    """

    :param class_name:
    :param form_schema_model:

    """
    return {
        "tags": [class_name],
        "description": f"Update several {class_name}",
        "requestBody": {
            "description": f"{class_name} request model",
            "required": True,
            "content": {"application/json": {"schema": form_schema_model}},
        },
        "responses": {
            "200": {"description": f"{class_name} response model", "content": {"application/json": {"schema": form_schema_model}}},
            "400": {"description": "Operation fail", "content": {"application/json": {"schema": error_swagger_schema}}},
            "500": {"description": "Operation fail", "content": {"application/json": {"schema": error_swagger_schema}}},
        },
    }


def get_query_endpoint_schema(
    class_name: str, tags: list, query_parameters: List, description: str = None, request_schema: dict = None, response_schema: dict = None
):
    """

    :param class_name: str:
    :param tags: list:
    :param query_parameters: List:
    :param description: str:  (Default value = None)
    :param request_schema: dict:  (Default value = None)
    :param response_schema: dict:  (Default value = None)

    """
    schema = {
        "tags": tags,
        "description": description,
        "responses": {
            "200": {
                "description": f"{class_name} response model",
                "content": {"application/json": {"schema": response_schema} if response_schema else {"type": "object"}},
            },
            "404": {"description": "Not found response model", "content": {"application/json": {"schema": not_found_swagger_schema}}},
            "500": {"description": "Operation fail", "content": {"application/json": {"schema": error_swagger_schema}}},
        },
    }

    if query_parameters:
        schema["parameters"] = query_parameters

    if request_schema:
        schema["requestBody"] = {"required": True, "content": {"application/json": {"schema": request_schema}}}
    return schema


def get_delete_list_endpoint_schema(class_name, request_body_schema):
    """

    :param class_name:
    :param request_body_schema:

    """
    return {
        "tags": [class_name],
        "description": f"Delete several {class_name}",
        "requestBody": {
            "description": f"Delete {class_name} list request model",
            "required": True,
            "content": {"application/json": {"schema": request_body_schema}},
        },
        "responses": {
            "200": {"description": f"{class_name} response model", "content": {"application/json": {"schema": {"type": "string", "example": "ok"}}}},
            "400": {"description": "Operation fail", "content": {"application/json": {"schema": error_swagger_schema}}},
            "500": {"description": "Operation fail", "content": {"application/json": {"schema": error_swagger_schema}}},
        },
    }
