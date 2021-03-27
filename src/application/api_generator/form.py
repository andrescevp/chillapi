from flask_restful_swagger_3 import Schema as SwaggerSchema
import json
from sqlalchemy_filters import apply_filters, apply_sort, apply_pagination, apply_loads
from alchemyjsonschema import SchemaFactory, ForeignKeyWalker
from wtforms.ext.sqlalchemy.orm import model_form
from src.application.jsonschema import WTFormToJSONSchema
from flask_wtf import FlaskForm
from wtforms_alchemy import model_form_factory

# @see https://pypi.org/project/sqlalchemy-filters/

ModelForm = model_form_factory(FlaskForm)

class FilterModel(SwaggerSchema):
    type = 'object'
    properties = {
        'field': {
            'type': 'string'
        },
        'op': {
            'type': 'string',
            "enum": [
                'is_null'
                'is_not_null',
                '==',
                'eq',
                '!=',
                'ne',
                '>',
                'gt',
                '<',
                'lt',
                '>=',
                'ge',
                '<=',
                'le',
                'like',
                'ilike',
                'not_ilike',
                'in',
                'not_in',
                'any',
                'not_any',
            ],

        },
        'value': {
            'type': 'array',
            'description': 'array of values to filter. When operations are not "in", "not_in", "any", "not_any" the array must be an array with only one element',
            'items': [{'type': 'string'}]
        }
    }
    required = ['field', 'op']

class OrderByModel(SwaggerSchema):
    type = 'object'
    properties = {
        'field': {
            'type': 'string'
        },
        'direction': {
            'type': 'string'
        }
    }
    required = ['field', 'direction']

def get_filtering(args):
    page = 1
    per_page = 10
    filters = []
    order_by = []
    args_len = len(args)
    start = 0
    filter_pos = 0
    sort_pos = 0
    if "page" in args:
        page = int(args.get("page"))
    if "per_page" in args:
        per_page = int(args.get("per_page"))
    while start < args_len:
        if f"filters[{filter_pos}]" in args:
            data_str = args.get(f"filters[{filter_pos}]")
            filters.insert(filter_pos, json.loads(data_str))
            filter_pos += 1
        if f"order_by[{sort_pos}]" in args:
            data_str = args.get(f"order_by[{sort_pos}]")
            order_by.insert(sort_pos, json.loads(data_str))
            sort_pos += 1
        start += 1
    return filters, page, per_page, order_by

def get_filtered_response(filters, order_by, page, per_page, query, schema):
    query, pagination = apply_pagination(query, page_number=int(page), page_size=int(per_page))
    for filter in filters:
        query = apply_filters(query, filter)
    for sorting in order_by:
        query = apply_sort(query, sorting)
    list = query.all()
    page_size, page_number, num_pages, total_results = pagination
    response = {
        'items': schema.dump(list),
        'page': page,
        'per_page': page_size,
        'num_pages': num_pages,
        'total_results': total_results,
        'filters': filters,
        'order_by': order_by,
    }
    return response

def generate_swagger_properties(object, remove_id_field = False):
    factory = SchemaFactory(ForeignKeyWalker) # or NoForeignKeyWalker
    schema = factory(object)
    properties = schema['properties']

    if remove_id_field and 'id' in properties:
        del properties['id']

    return properties

def generate_form(model, session = None, exclude = None):
    return model_form(model, db_session=session, exclude=exclude, base_class=FlaskForm)

def generate_form_schema_from_model(model, session = None, exclude = None):
    form = generate_form(model, session, exclude)
    schema_repr = WTFormToJSONSchema().convert_form(form)
    return schema_repr['properties']

def generate_form_schema_from_form(form, object = None):
    if object == None:
        object = {}

    schema_repr = WTFormToJSONSchema().convert_form(form)
    for property in schema_repr['properties']:
        if hasattr(form, property):
            prop = getattr(form, property)
            schema_repr['properties'][property]['data'] = prop.data if hasattr(prop, 'data') else None

    return schema_repr['properties']


'''
We need this function to create dynamically the form class to can interact with the same db session
formClass = getFormClass()
form = formCLass()
form = formCLass(obj=Model)
form = formCLass(obj=Model)
'''
def getFormClass(entity, class_name=None, form_custom_properties=None):
    if form_custom_properties == None:
        form_custom_properties = []

    class Form(ModelForm):
        class Meta:
            model = entity



    for key in form_custom_properties:
        setattr(Form, key, form_custom_properties[key]())
    Form.__name__ = f'{class_name}Form'

    return Form