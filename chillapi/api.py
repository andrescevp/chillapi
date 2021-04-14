import os

from flask import Flask
from flask_cors import CORS
from flask_request_id_header.middleware import RequestID
from flask_restful_swagger_3 import Api
from swagger_ui import api as api_doc

from chillapi.logger.app_loggers import logger
from chillapi.manager import FlaskApiManager
from chillapi.app.config import api_config, config
from chillapi.app.error_handlers import register_error_handlers
from chillapi.extensions.audit import register_audit_handler
from chillapi.app.sitemap import register_routes as register_routes_sitemap
from flask_sqlalchemy import get_debug_queries

api_manager = FlaskApiManager(config)


def ChillApi(app: Flask = None):
    if app is None:
        app = Flask(api_config['app']['name'])

    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('APP_DB_URL')
    app.config['SECRET_KEY'] = os.environ.get('APP_SECRET_KEY')
    app.config['WTF_CSRF_ENABLED'] = False
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
    app.config['REQUEST_ID_UNIQUE_VALUE_PREFIX'] = None
    register_error_handlers(app)
    CORS(app)
    RequestID(app)
    api = Api(app, version=api_config['app']['version'], api_spec_url=api_config['app']['swagger_url'])
    api_doc.RestfulApi(app, title=api_config['app']['name'], doc=api_config['app']['swagger_ui_url'],
                       config={  # Swagger UI config overrides
                           'app_name': api_config['app']['name']
                       })

    api_manager.create_api(api)

    register_audit_handler(app)
    register_routes_sitemap(app)

    if api_config['app']['debug']:
        from werkzeug.middleware.profiler import ProfilerMiddleware
        app.config['PROFILE'] = True
        app.wsgi_app = ProfilerMiddleware(app.wsgi_app, restrictions=[30], profile_dir='./profile')

    return app, api, api_manager, api_config

# def sql_debug(response):
#     queries = list(get_debug_queries())
#     query_str = ''
#     total_duration = 0.0
#     for q in queries:
#         total_duration += q.duration
#         stmt = str(q.statement % q.parameters).replace('\n', '\n       ')
#         query_str += 'Query: {0}\nDuration: {1}ms\n\n'.format(stmt, round(q.duration * 1000, 2))
#
#     print '=' * 80
#     print ' SQL Queries - {0} Queries Executed in {1}ms'.format(len(queries), round(total_duration * 1000, 2))
#     print '=' * 80
#     print query_str.rstrip('\n')
#     print '=' * 80 + '\n'
#
#     return response