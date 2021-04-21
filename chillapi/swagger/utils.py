from chillapi.app.flask_restful_swagger_3 import Schema
from chillapi.database.query_builder import sql_operators


class ColumnSwaggerDefinition:
    column_swagger_properties = {}

    def __init__(self, name: str, column_swagger_properties: dict):
        self.name = name
        self.column_swagger_properties = column_swagger_properties


def get_filter_schema(class_name) -> Schema:
    _ops = [str(o) for o in sql_operators.keys()]

    class FilterModel(Schema):
        type = "object"
        properties = {
            "op": {
                "type": "string",
                "enum": _ops,
            },
            "value": {"type": "string"},
        }
        required = ["value", "op"]

    FilterModel.__name__ = f"{class_name}FilterModel"

    return FilterModel


def get_order_schema(class_name):
    class OrderByModel(Schema):
        type = "object"
        properties = {"field": {"type": "array", "items": {"type": "string"}}, "direction": {"type": "string", "enum": ["asc", "desc"]}}
        required = ["field", "direction"]

    OrderByModel.__name__ = f"{class_name}OrderByModel"

    return OrderByModel


def get_size_schema(class_name):
    class SizeListModel(Schema):
        type = "object"
        properties = {"limit": {"type": "integer", "default": 100}, "offset": {"type": "integer", "default": 0}}
        required = ["limit", "offset"]

    SizeListModel.__name__ = f"{class_name}LimitOffsetListModel"

    return SizeListModel


def python_to_swagger_types(python_type):
    switcher = {
        "str": "string",
        "int": "integer",
        "float": "number",
        "complex": "number",
        "datetime.datetime": "string",
        "datetime": "string",
        "dict": "object",
        "bool": "boolean",
    }
    return switcher.get(python_type, "string")


def columns_map_to_swagger_properties(columns_map, columns_swagger_definition: dict = None):
    properties = {}

    for property_name, column_info in columns_map.items():
        properties[property_name] = {"type": python_to_swagger_types(column_info["type"].python_type.__name__)}

        if columns_swagger_definition:
            _props = columns_swagger_definition[property_name].column_swagger_properties
            properties[property_name] = {**properties[property_name], **_props}
    return properties


def get_response_swagger_schema(columns_map: dict, class_name: str, columns_swagger_definition: dict = None):
    columns_as_properties = columns_map_to_swagger_properties(columns_map, columns_swagger_definition)

    class ResponseModel(Schema):
        type = "object"
        properties = columns_as_properties

    ResponseModel.__name__ = f"{class_name}ResponseModel"

    return ResponseModel


def get_form_array_swagger_schema(
    class_name: str, form_schema: type(Schema), class_name_postfix: str = "ArrayFormModel", min_items: int = 1, max_items: int = 100
):
    class ArrayFormModel(Schema):
        type = "array"
        items = form_schema
        minItems = min_items
        maxItems = max_items

    ArrayFormModel.__name__ = f"{class_name}{class_name_postfix}"

    return ArrayFormModel


def get_list_filtered_response_swagger_schema(columns_map: dict, request_schema: dict, class_name: str, columns_swagger_definition: dict = None):
    columns_as_properties = columns_map_to_swagger_properties(columns_map, columns_swagger_definition)

    meta = {v["name"]: {"type": "object", "schema": v["schema"]} for v in request_schema}

    meta["total_records"] = {"type": "integer"}

    class ResponseModel(Schema):
        type = "object"
        properties = {
            "data": {"type": "array", "items": {"type": "object", "properties": columns_as_properties}},
            "_meta": {"type": "object", "properties": meta},
        }

    ResponseModel.__name__ = f"{class_name}ListResponseModel"

    return ResponseModel


def get_list_filtered_request_swagger_schema(class_name: str, columns_map: dict):
    schema = []
    for property_name, column_info in columns_map.items():
        schema.append({"in": "query", "name": property_name, "allowEmptyValue": True, "schema": get_filter_schema(class_name)})

    schema.append({"in": "query", "name": "order", "allowEmptyValue": True, "required": False, "schema": get_order_schema(class_name)})

    schema.append({"in": "query", "name": "size", "allowEmptyValue": True, "required": False, "schema": get_size_schema(class_name)})

    return schema


def get_revisable_response_swagger_schema():
    class RevisableOperationResponseModel(Schema):
        type = "object"
        properties = {
            "message": {
                "type": "string",
                "enum": ["ok", "errors"],
            },
            "details": {"type": "array", "items": [{"type": "string"}]},
        }

    return RevisableOperationResponseModel


def get_error_swagger_schema():
    class ErrorResponseModel(Schema):
        type = "object"
        properties = {
            "code": {
                "type": "integer",
            },
            "description": {
                "type": "string",
            },
        }

    return ErrorResponseModel


def get_not_found_swagger_schema():
    class NotFoundResponseModel(Schema):
        type = "object"
        properties = {
            "message": {
                "type": "string",
            }
        }

    return NotFoundResponseModel


def get_request_swagger_schema(columns_map: dict, class_name: str, columns_swagger_definition: dict = None, required_fields=None):
    columns_as_properties = columns_map_to_swagger_properties(columns_map, columns_swagger_definition)

    class RequestModel(Schema):
        type = "object"
        properties = columns_as_properties
        required = required_fields

    RequestModel.__name__ = f"{class_name}RequestModel"

    return RequestModel
