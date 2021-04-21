_app_defaults = {
        'name':           'api',
        'version':        '0.0',
        'swagger_url':    '/swagger',
        'swagger_ui_url': '/doc',
        'host':           '0.0.0.0',
        'port':           8000,
        'debug':          True,
        }

_environment_defaults = {
        'APP_DB_URL':     None,
        'APP_SECRET_KEY': 'this-is-not-so-secret',
        }

_logger_defaults = {
        'app':           {
                'output': 'stdout',
                'level':  10,
                },
        'audit_logger':  {
                'output': 'stdout',
                'level':  10,
                },
        'error_handler': {
                'output': 'stdout',
                'level':  10,
                },
        'sqlalchemy':    {
                'output': 'stdout',
                'level':  10,
                },
        }

_database_defaults = {
        'name':      None,
        'schema':    'public',
        'defaults':  {
                'tables': {
                        'id_field':        'id',
                        'fields_excluded': {
                                'all':  None,
                                'GET':  {
                                        'SINGLE': None,
                                        'LIST':   None,
                                        },
                                'PUT':  {
                                        'SINGLE': None,
                                        'LIST':   None,
                                        },
                                'POST': {
                                        'SINGLE': None,
                                        'LIST':   None,
                                        },
                                },
                        'api_endpoints':   {
                                'PUT':    ['SINGLE', 'LIST'],
                                'GET':    ['SINGLE', 'LIST'],
                                'POST':   ['SINGLE', 'LIST'],
                                'DELETE': ['SINGLE', 'LIST'],
                                },
                        'extensions':      {
                                'soft_delete':         {
                                        'enable': False
                                        },
                                'on_update_timestamp': {
                                        'enable': False
                                        },
                                'on_create_timestamp': {
                                        'enable': False
                                        },
                                }
                        }
                },
        'tables':    [],
        'sql':       [],
        'templates': [],
        }

_tables_default_config = {
        'id_field':        'id',
        'fields_excluded': {
                'all': None
                },
        'GET':             {
                'SINGLE': None,
                'LIST':   None,
                },
        'POST':            {
                'SINGLE': None,
                'LIST':   None,
                },
        'PUT':             {
                'SINGLE': None,
                'LIST':   None,
                },
        'api_endpoints':   {
                'PUT':    ['SINGLE', 'LIST'],
                'GET':    ['SINGLE', 'LIST'],
                'POST':   ['SINGLE', 'LIST'],
                'DELETE': ['SINGLE', 'LIST'],
                },
        'extensions':      {
                'audit_logger':        {
                        'package':      'chillapi.extensions.audit',
                        'handler':      'NullAuditHandler',
                        'handler_args': {},
                        },
                'soft_delete':         {
                        'enable': False
                        },
                'on_update_timestamp': {
                        'enable': False
                        },
                'on_create_timestamp': {
                        'enable': False
                        },
                }
        }

_table_default_config = {
        'id_field':        'id',
        'alias':           None,
        'fields_excluded': {
                'all': None
                },
        'GET':             {
                'SINGLE': None,
                'LIST':   None,
                },
        'POST':            {
                'SINGLE': None,
                'LIST':   None,
                },
        'PUT':             {
                'SINGLE': None,
                'LIST':   None,
                },
        'api_endpoints':   {
                'PUT':    ['SINGLE', 'LIST'],
                'GET':    ['SINGLE', 'LIST'],
                'POST':   ['SINGLE', 'LIST'],
                'DELETE': ['SINGLE', 'LIST'],
                },
        'extensions':      {
                'soft_delete':         {
                        'enable': False
                        },
                'on_update_timestamp': {
                        'enable': False
                        },
                'on_create_timestamp': {
                        'enable': False
                        },
                }
        }

_sql_default_config = {
        'name':             None,
        'method':           'GET',
        'url':              None,
        'sql':              None,
        'query_parameters': None,
        'response_schema':  None,
        'request_schema':   None
        }

_sql_template_default_config = {
        'name':             None,
        'method':           'GET',
        'url':              None,
        'template':         None,
        'query_parameters': None,
        'response_schema':  None,
        'request_schema':   None
        }
