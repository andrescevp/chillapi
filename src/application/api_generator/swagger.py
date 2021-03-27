from alchemyjsonschema import SchemaFactory, ForeignKeyWalker

def generate_swagger_properties(object, remove_id_field=False):
    factory = SchemaFactory(ForeignKeyWalker)  # or NoForeignKeyWalker
    schema = factory(object)
    properties = schema['properties']

    if remove_id_field and 'id' in properties:
        del properties['id']

    return properties
