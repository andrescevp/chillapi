import json
import os
import pathlib

import simplejson
from flask import Flask
from flask_cors import CORS
from flask_request_id_header.middleware import RequestID
from jsonschema import validate, ValidationError
from openapi_spec_validator import default_handlers, JSONSpecValidatorFactory, SpecValidator
from openapi_spec_validator.readers import read_from_filename
from openapi_spec_validator.schemas import read_yaml_file
from six.moves.urllib import parse, request
from swagger_ui import api as api_doc

from chillapi.abc import AttributeDict
from chillapi.app.config import ApiConfig, ChillApiExtensions, ChillApiModuleLoader, CWD
from chillapi.app.error_handlers import register_error_handlers
from chillapi.app.file_utils import read_yaml
from chillapi.app.flask_restful_swagger_3 import Api, swagger
from chillapi.app.sitemap import register_routes as register_routes_sitemap
from chillapi.exceptions.api_manager import ConfigError
from chillapi.extensions.audit import register_audit_handler
from chillapi.logger.app_loggers import logger
from chillapi.logger.formatter import CustomEncoder
from chillapi.manager import FlaskApiManager

_CONFIG_FILE = f"{CWD}/api.yaml"


def ChillApi(app: Flask = None, config_file: str = _CONFIG_FILE, export_path: str = f"{CWD}/var"):
    """
    ChillApi Loader.
    :param app:
    :param config_file:
    :param export_path:
    """
    SCHEMA_CONFIG_FILE = os.path.realpath(f"{pathlib.Path(__file__).parent.absolute()}/../api.schema.json")
    api_config = read_yaml(config_file)
    api_schema = json.load(open(SCHEMA_CONFIG_FILE))

    try:
        validate(instance=api_config, schema=api_schema)
    except ValidationError as e:
        raise ConfigError(e)

    _app_name = api_config["app"]["name"]
    module_loader = ChillApiModuleLoader()

    set_api_security(api_config, module_loader)

    extensions = ChillApiExtensions(module_loader)
    config = ApiConfig(**{**api_config, **{"extensions": extensions}})
    db = config.db
    data_repository = config.repository

    api_manager = FlaskApiManager(config)

    if app is None:
        app = Flask(_app_name)

    register_error_handlers(app)
    app.config["BASE_DIR"] = CWD
    app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("APP_DB_URL")
    app.config["SECRET_KEY"] = os.environ.get("APP_SECRET_KEY")
    app.config["WTF_CSRF_ENABLED"] = False
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = True
    app.config["TRAP_HTTP_EXCEPTIONS"] = True
    app.config["TRAP_BAD_REQUEST_ERRORS"] = True
    app.config["REQUEST_ID_UNIQUE_VALUE_PREFIX"] = None
    CORS(app)
    RequestID(app)
    api = Api(
        app,
        security_level=api_config["app"]["security_level"] if "security_level" in api_config["app"] else "STANDARD",
        version=api_config["app"]["version"],
        api_spec_url=api_config["app"]["swagger_url"],
        security=api_config["app"]["security"] if "security" in api_config["app"] else None,
        license=api_config["app"]["license"] if "license" in api_config["app"] else None,
        contact=api_config["app"]["contact"] if "contact" in api_config["app"] else None,
        externalDocs=api_config["app"]["externalDocs"] if "externalDocs" in api_config["app"] else None,
        components={"securitySchemes": api_config["app"]["securitySchemes"] if "securitySchemes" in api_config["app"] else None},
    )

    api_doc.RestfulApi(app, title=_app_name, doc=api_config["app"]["swagger_ui_url"], config={"app_name": _app_name})  # Swagger UI config overrides

    api_spec_file = f"{CWD}/var/api_spec.json"

    if not os.path.exists(api_spec_file):
        import requests

        url = "https://raw.githubusercontent.com/OAI/OpenAPI-Specification/main/schemas/v3.1/schema.yaml"  # noqa E501
        r = requests.get(url, allow_redirects=True)
        open(api_spec_file, "wb").write(r.content)

    path_full = api_spec_file
    schema_v3 = read_yaml_file(path_full)
    schema_v3_url = parse.urljoin("file:", request.pathname2url(path_full))

    openapi_v3_validator_factory = JSONSpecValidatorFactory(
        schema_v3,
        schema_v3_url,
        resolver_handlers=default_handlers,
    )

    openapi_v3_spec_validator = SpecValidator(
        openapi_v3_validator_factory,
        resolver_handlers=default_handlers,
    )

    simplejson.dump(api.get_swagger_doc(), open(f"{export_path}/{_app_name}_swagger.json", "w"), indent=2, cls=CustomEncoder, for_json=True)

    spec_dict, spec_url = read_from_filename(f"{export_path}/{_app_name}_swagger.json")

    # If no exception is raised by validate_spec(), the spec is valid.
    # do not stop the execution but show a critical
    errors_iterator = openapi_v3_spec_validator.iter_errors(spec_dict)
    for _ie, err in enumerate(errors_iterator):
        logger.critical(err)

    simplejson.dump(config.to_dict(), open(f"{export_path}/{_app_name}_api.config.json", "w"), indent=2, cls=CustomEncoder, for_json=True)

    api_manager.create_api(api)
    register_audit_handler(app, extensions.get_extension("audit"))

    if api_config["app"]["debug"]:
        from werkzeug.middleware.profiler import ProfilerMiddleware

        app.config["PROFILE"] = True
        app.config["DEBUG"] = True

        def filename_format(env):
            return "{uuid}.prof".format(uuid=env["HTTP_X_REQUEST_ID"])

        app.wsgi_app = ProfilerMiddleware(app.wsgi_app, restrictions=[30], profile_dir="./profile", filename_format=filename_format)

        register_routes_sitemap(app)

    return AttributeDict(
        {
            "app": app,
            "api": api,
            "api_manager": api_manager,
            "api_config": api_config,
            "db": db,
            "data_repository": data_repository,
            "module_loader": module_loader,
            "table_extensions": extensions,
        }
    )


def set_api_security(api_config, module_loader):
    if "securitySchemes" in api_config["app"] and len(api_config["app"]["securitySchemes"].keys()) > 0:
        if "security_handler" not in api_config["app"]:
            raise ConfigError("security_handler not defined")

        module_loader.add_module(api_config["app"]["security_handler"]["package"])

        def auth(request_obj, endpoint, method):
            security_schemes = api_config["app"]["securitySchemes"]
            security = api_config["app"]["security"]
            # print(request_obj.headers)
            is_auth = module_loader.get_module_attr(
                api_config["app"]["security_handler"]["package"],
                api_config["app"]["security_handler"]["handler"],
                {
                    "request_obj": request_obj,
                    "endpoint": endpoint,
                    "method": method,
                    "security_schemes": security_schemes,
                    "security": security,
                },
            )
            return is_auth

        swagger.auth = auth
