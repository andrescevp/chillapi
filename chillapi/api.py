import json
import os
import pathlib

import simplejson
from flask import Flask
from flask_cors import CORS
from flask_request_id_header.middleware import RequestID
from flask_restful_swagger_3 import Api
from openapi_spec_validator.schemas import read_yaml_file
from swagger_ui import api as api_doc
from jsonschema import validate, ValidationError

from chillapi.exceptions.api_manager import ConfigError
from chillapi.logger.formatter import CustomEncoder
from chillapi.manager import FlaskApiManager
from chillapi.app.config import CWD, ChillApiModuleLoader, TableExtensions, ApiConfig
from chillapi.app.file_utils import read_yaml
from chillapi.app.error_handlers import register_error_handlers
from chillapi.extensions.audit import register_audit_handler
from chillapi.app.sitemap import register_routes as register_routes_sitemap

_CONFIG_FILE = f'{CWD}/api.yaml'


def ChillApi(app: Flask = None, config_file: str = _CONFIG_FILE, export_path: str = CWD):
    SCHEMA_CONFIG_FILE = os.path.realpath(f'{pathlib.Path(__file__).parent.absolute()}/../api.schema.json')
    api_config = read_yaml(config_file)
    api_schema = json.load(open(SCHEMA_CONFIG_FILE, 'r'))

    try:
        validate(instance=api_config, schema=api_schema)
    except ValidationError as e:
        raise ConfigError(e)

    _app_name = api_config['app']['name']

    module_loader = ChillApiModuleLoader()
    table_extension = TableExtensions(module_loader)
    config = ApiConfig(**{**api_config, **{'table_extensions': table_extension}})
    db = config.db
    data_repository = config.repository

    api_manager = FlaskApiManager(config)

    if app is None:
        app = Flask(_app_name)

    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('APP_DB_URL')
    app.config['SECRET_KEY'] = os.environ.get('APP_SECRET_KEY')
    app.config['WTF_CSRF_ENABLED'] = False
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
    app.config['REQUEST_ID_UNIQUE_VALUE_PREFIX'] = None
    register_error_handlers(app)
    CORS(app)
    RequestID(app)
    api = Api(app,
              version=api_config['app']['version'],
              api_spec_url=api_config['app']['swagger_url'],
              security=api_config['app']['security'],
              license=api_config['app']['license'],
              contact=api_config['app']['contact'],
              externalDocs=api_config['app']['externalDocs'],
              components={'securitySchemes': api_config['app']['securitySchemes']}
              )
    _api_doc = api_doc.RestfulApi(
        app,
        title=_app_name,
        doc=api_config['app']['swagger_ui_url'],
        config={  # Swagger UI config overrides
            'app_name': _app_name
        }
    )

    api_manager.create_api(api)
    register_audit_handler(app, table_extension.get_extension('audit'))
    register_routes_sitemap(app)

    if api_config['app']['debug']:
        from werkzeug.middleware.profiler import ProfilerMiddleware
        from openapi_spec_validator.readers import read_from_filename
        from openapi_spec_validator import get_openapi_schema, JSONSpecValidatorFactory, default_handlers, SpecValidator
        from pkg_resources import resource_filename
        from six.moves.urllib import parse, request

        api_spec_file = f'{CWD}/var/api_spec.json'
        if not os.path.exists(api_spec_file):
            import requests
            url = 'https://raw.githubusercontent.com/OAI/OpenAPI-Specification/main/schemas/v3.1/schema.yaml'
            r = requests.get(url, allow_redirects=True)
            open(api_spec_file, 'wb').write(r.content)

        path_full = api_spec_file
        schema_v3 = read_yaml_file(path_full)
        schema_v3_url = parse.urljoin('file:', request.pathname2url(path_full))

        openapi_v3_validator_factory = JSONSpecValidatorFactory(
            schema_v3, schema_v3_url,
            resolver_handlers=default_handlers,
        )

        openapi_v3_spec_validator = SpecValidator(
            openapi_v3_validator_factory,
            resolver_handlers=default_handlers,
        )

        app.config['PROFILE'] = True
        app.wsgi_app = ProfilerMiddleware(app.wsgi_app, restrictions=[30], profile_dir='./profile')

        simplejson.dump(api.get_swagger_doc(), open(f'{export_path}/{_app_name}_swagger.json', 'w'), indent=2,
                        cls=CustomEncoder,
                        for_json=True)

        spec_dict, spec_url = read_from_filename(f'{export_path}/{_app_name}_swagger.json')

        # If no exception is raised by validate_spec(), the spec is valid.
        errors_iterator = openapi_v3_spec_validator.iter_errors(spec_dict)
        for _ie, err in enumerate(errors_iterator):
            print(err)

        simplejson.dump(config.to_dict(), open(f'{export_path}/{_app_name}_api.config.json', 'w'), indent=2,
                        cls=CustomEncoder,
                        for_json=True)

    return app, api, api_manager, api_config, db, data_repository
