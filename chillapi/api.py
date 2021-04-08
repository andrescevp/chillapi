from flask import Flask
from flask_cors import CORS
from flask_request_id_header.middleware import RequestID
from flask_restful_swagger_3 import Api
from swagger_ui import api as api_doc

from chillapi.manager import FlaskTableApiManager
from chillapi.app.config import api_config, _set_logger_config, _get_db_url, _get_secret_key
from chillapi.app.error_handlers import register_error_handlers
from chillapi.database.connection import db
from chillapi.extensions.audit import register_audit_handler
from chillapi.app.sitemap import register_routes as register_routes_sitemap


def ChillApi(app: Flask = None):
    logger_config = api_config['logger']
    audit_logger = api_config['app']['audit_logger'] if 'audit_logger' in api_config['app'] else None
    _set_logger_config(logger_config, audit_logger, api_config['app']['debug'])

    if app is None:
        app = Flask(api_config['app']['name'])

    db_url = _get_db_url(api_config)
    secret = _get_secret_key(api_config)

    app.config['SQLALCHEMY_DATABASE_URI'] = db_url  # new
    app.config['SECRET_KEY'] = secret
    app.config['WTF_CSRF_ENABLED'] = False
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
    app.config['REQUEST_ID_UNIQUE_VALUE_PREFIX'] = None
    register_error_handlers(app)
    CORS(app)
    RequestID(app)

    # db = SQLAlchemy(app)
    # app.app_context().push()

    api = Api(app, version=api_config['app']['version'], api_spec_url=api_config['app']['swagger_url'])
    api_doc.RestfulApi(app, title=api_config['app']['name'], doc=api_config['app']['swagger_ui_url'],
                       config={  # Swagger UI config overrides
                           'app_name': api_config['app']['name']
                       })

    api_manager = FlaskTableApiManager(
        api_config['database']['name'],
        api_config['database']['schema'],
        api_config['database']['defaults']['tables']['fields_excluded'] if 'fields_excluded' in
                                                                           api_config['database']['defaults'][
                                                                               'tables'] else {},
        api_config['database']['defaults']['tables']['api_endpoints'] if 'api_endpoints' in
                                                                         api_config['database']['defaults'][
                                                                             'tables'] else {},
        api_config['database']['defaults']['tables']['extensions'] if 'extensions' in
                                                                      api_config['database']['defaults'][
                                                                          'tables'] else {},
        api_config['database']['tables'],
        api_config['database']['sql'],
        api_config['database']['templates'],
        db,
        db_url
    )

    api_manager.create_api(api)
    register_audit_handler(app, audit_logger)
    register_routes_sitemap(app)

    return app, api, api_manager, api_config
