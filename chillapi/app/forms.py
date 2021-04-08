import json

import wtforms_json

from wtforms import StringField, IntegerField, FloatField, DateTimeField, BooleanField, Form, fields, \
    Field
from wtforms.validators import DataRequired, ValidationError
from chillapi.swagger.jsonschema import WTFormToJSONSchema
from chillapi.swagger.utils import get_form_array_swagger_schema
from flask_restful_swagger_3 import Schema as SwaggerSchema

wtforms_json.init()
wtform_to_swagger_schema = WTFormToJSONSchema()


class JSONField(fields.Field):
    def _value(self):
        return json.dumps(self.data) if self.data else ''

    def process_formdata(self, valuelist):
        if valuelist:
            value = valuelist[0]
            try:
                self.data = json.loads(value)
            except ValueError:
                raise ValidationError('This field contains invalid JSON')
        else:
            self.data = None

    def pre_validate(self, form):
        super().pre_validate(form)
        if self.data:
            if type(self.data) == str:
                if self.data[0] not in {'{', '['} and self.data[-1] not in {'}', ']'}:
                    raise ValidationError('This field contains invalid JSON')

                try:
                    self.data = json.loads(self.data)
                except TypeError:
                    raise ValidationError('This field contains invalid JSON')
            else:
                try:
                    json.dumps(self.data)
                except TypeError:
                    raise ValidationError('This field contains invalid JSON')


def generate_form_swagger_schema_from_form(method: str, form: Form, as_array=False):
    form_schema = wtform_to_swagger_schema.convert_form(form)
    form_schema['description'] = f'{form.__name__} Form validated model'

    form_schema_model = type(
        f'{form.__name__}{method.replace("_", " ").title().replace(" ", "")}RequestModel',
        (SwaggerSchema,),
        form_schema
    )

    if as_array is False:
        return form_schema_model

    return get_form_array_swagger_schema(form.__name__, form_schema_model, 'ListRequestModel')


def column_to_flask_form_property(column_name: str, column_info) -> Field:
    validators = []

    if column_info.not_null is True:
        validators.append(DataRequired())

    switcher = {
        'str': StringField(column_name, validators, _name=column_name),
        'int': IntegerField(column_name, validators, _name=column_name),
        'float': FloatField(column_name, validators, _name=column_name),
        'complex': FloatField(column_name, validators, _name=column_name),
        'datetime.datetime': DateTimeField(column_name, validators, _name=column_name),
        'dict': JSONField(column_name, validators, _name=column_name),
        'bool': BooleanField(column_name, validators, _name=column_name)
    }

    return switcher.get(column_info.pytype.__name__, StringField(column_name))


def create_form_class(class_name: str, method: str, columns_map: dict):
    class FormResource(Form):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            # for column_name, column_info in columns_map.items():
            #     property_type = column_to_flask_form_property(column_name, column_info)
            #     setattr(self, column_name, property_type)
            #     self._fields[column_name] = property_type

        def for_json(self) -> dict:
            return self.data

    for column_name, column_info in columns_map.items():
        property_type = column_to_flask_form_property(column_name, column_info)
        setattr(FormResource, column_name, property_type)

    FormResource.__name__ = f'{class_name}{method.replace("_", " ").title().replace(" ", "")}Form'

    return FormResource
