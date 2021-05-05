# ChillApi

## DEMO

https://github.com/andrescevp/chillapi-demo

## Motivation

This project was born to increase the speed of delivery and development of APIs.

The premise is simple, not all roles can feel comfortable swimming in a sea of indented code, however they do feel comfortable in SQL languages. And those who do feel comfortable programming may prefer to use a tool that configures and propagates information than extending an ORM, routes, forms, etc; thus being able to spend more time on other types of tasks.

The connection and execution of queries is done in raw, that is, there is no ORM involved.

The implementation of this framework is on Flask using a series of additional libraries and adopting others to satisfy the requirements of the same.

# setup

Create a `api.yaml` file:
```yaml
app:
  name: ChillApi
  version: '0.1'
  swagger_url: '/swagger'
  swagger_ui_url: '/doc'
  host: 0.0.0.0
  port: 8000
  debug: True
  #  externalDocs:
  #    description: Find more info here
  #    url: https://example.com
  #  license:
  #    name: Apache 2.0
  #    url: https://www.apache.org/licenses/LICENSE-2.0.html
  #  contact:
  #    name: API Support
  #    url: http://www.example.com/support
  #    email: support@example.com
  securitySchemes:
    bearerAuth: # arbitrary name for the security scheme
      type: http
      scheme: bearer
      bearerFormat: JWT
  security:
    - bearerAuth: [ ]
  security_level: STANDARD
  security_handler:
    package: my_app.auth
    handler: auth
environment:
  __CHILLAPI_DB_DSN__: '$DB_URL'
#  __CHILLAPI_DB_DSN__: 'sqlite:///var/db.sqlite'
  __CHILLAPI_APP_SECRET_KEY__: 'super-secret-key'
logger:
  app:
    output: stdout
    level: 10
  audit_logger:
    output: stdout
    level: 40
  error_handler:
    output: stdout
    level: 40
  sqlalchemy:
    output: stdout
    level: 40
database:
  schema: public
  defaults:
    tables:
      id_field: id
      fields_excluded: # silent check if exists in the table
        all:
          - created_at
          - updated_by
          - updated_at
          - created_by
          - deleted_at
          - deleted_by
        GET:
          SINGLE: [ ] # request only
          LIST: [ ] # request only
        POST:
          SINGLE:
            - id
          LIST: [ ]
        PUT:
          SINGLE:
            - id
          LIST:
            - id
      api_endpoints:
        PUT: [ SINGLE, LIST ]
        GET: [ SINGLE, LIST ]
        POST: [ SINGLE, LIST ]
        DELETE: [ SINGLE, LIST ]
      extensions:
        audit_logger:
          package: my_app.audit
          handler: MyAuditHandler
          handler_args:
            name: hello
        soft_delete:
          enable: True
          default_field: deleted_at
        on_update_timestamp:
          enable: True
          default_field: updated_at
        on_create_timestamp:
          enable: True
          default_field: created_at
  tables:
    - name: book_category
      #      alias: ~
      #      id_field: ~ # id by default
      extensions:
        soft_delete:
          cascade:
            one_to_many:
              - table: book
                column_id: id
                column_fk: book_category_id
    - name: book
      #      alias: ~
      #      id_field: ~ # id by default
      #      extensions:
      #        soft_delete:
      #          enable: False
      fields_excluded: # extends defaults
        #        all: [ ]
        #        GET:
        #          SINGLE:
        #            - name
        #          LIST: [ ]
        POST:
          SINGLE:
            - isin
    #          LIST: [ ]
    #        PUT:
    #          SINGLE:
    #            - name
    #          LIST: [ ]
    #        DELETE:
    #          SINGLE: [ ]
    #          LIST: [ ]
    #      api_endpoints:   #overwrite defaults
    #        GET: [ SINGLE ]
    - name: author
      #      alias: ~
      #      id_field: iso
      extensions:
        after_response:
          package: my_app.default_events
          handler: MyAfterResponseEvent
        before_response:
          package: my_app.default_events
          handler: MyBeforeResponseEvent
        soft_delete:
          cascade:
            many_to_many:
              - table: author
                column_id: id
                join_table: book_has_author
                join_columns:
                  main: author_id
                  join: book_id
        validators:
          asin:
            - package: wtforms.validators
              handler: Length
              handler_args:
                min: 5
                max: 100
      fields_excluded:
        #        all: []
        GET:
          SINGLE:
            - name
      #          LIST: [ ]
      #        POST:
      #          SINGLE: []
      #          LIST: [ ]
      #        PUT:
      #          SINGLE: []
      #          LIST: [ ]
      #        DELETE:
      #          SINGLE: [ ]
      #          LIST: [ ]
      api_endpoints: { }
    - name: dummy
      #      alias: ~
      #      id_field: ~
      extensions:
        soft_delete:
          enable: False
        on_update_timestamp:
          enable: False
        on_create_timestamp:
          enable: False
      #      fields_excluded:
      #        all: [ ]
      #        GET:
      #          SINGLE: [ ]
      #          LIST: [ ]
      #        POST:
      #          SINGLE: [ ]
      #          LIST: [ ]
      #        PUT:
      #          SINGLE: [ ]
      #          LIST: [ ]
      #        DELETE:
      #          SINGLE: [ ]
      #          LIST: [ ]
      api_endpoints: { }
    - name: dummy_create
      #      alias: ~
      #      id_field: ~
      extensions:
        soft_delete:
          enable: False
        on_update_timestamp:
          enable: False
        on_create_timestamp:
          enable: True
          default_field: creation
      #      fields_excluded:
      #        all: [ ]
      #        GET:
      #          SINGLE: [ ]
      #          LIST: [ ]
      #        POST:
      #          SINGLE: [ ]
      #          LIST: [ ]
      #        PUT:
      #          SINGLE: [ ]
      #          LIST: [ ]
      #        DELETE:
      #          SINGLE: [ ]
      #          LIST: [ ]
      api_endpoints:
        GET: [ SINGLE, LIST ]
  sql:
    - name: tests
      method: GET
      url: /tests/test_sql
      sql: |
        select * from author
      query_parameters: [ ] # swagger schema for url query parameters in sql
      response_schema:
        type: object
    #        parameters:
    #          test:
    #            type: string
    - name: tests 2
      method: GET
      url: /tests/test_sql2
      sql: |
        select c.name as book_name, cr.*
        from book c
        inner join book_category cr ON cr.id = c.book_category_id AND c.name = :name
      query_parameters: # swagger schema for url query parameters in sql
        - in: query
          name: name
          #          required: true
          schema:
            type: string
    - name: test_params
      method: POST
      url: /test_params_post
      sql: |
        select c.name as book_name, cr.*
        from book c
        inner join book_category cr ON cr.id = c.book_category_id AND c.name = :name
      request_schema: # swagger schema for url query parameters in sql
        type: object
        properties:
          name:
            type: string
  #            required: true
  templates:
    - name: tests
      method: GET
      url: /test_template # swagger route format
      template: ./api_sql_templates/test.sql
      query_parameters: [ ] # swagger schema for url query parameters in sql
    - name: test_params
      method: GET
      url: /test_template_params
      template: ./api_sql_templates/test_params.sql
      query_parameters: # swagger schema for url query parameters in sql
        - in: query
          name: name
          #          required: true
          schema:
            type: string
    - name: test_params
      method: GET
      url: /test_template_params_url/<name>
      template: ./api_sql_templates/test_params.sql
      query_parameters: # swagger schema for url query parameters in sql
        - in: path
          name: name
          required: true
    #          schema:
    #            type: string
    - name: test_params
      method: POST
      url: /test_template_params
      template: ./api_sql_templates/test_params.sql
      request_schema: # swagger schema for url query parameters in sql
        type: object
        properties:
          name:
            type: string
```

Create your app.py file
```python
from chillapi.api import ChillApi

_resources = ChillApi()
app = _resources.app
api_config = _resources.api_config
if __name__ == '__main__':
    app.run(
        debug=api_config['app']['debug'],
        host=api_config['app']['host'],
        port=api_config['app']['port']
    )
```

Run your app
```shell
python gunicorn --bind 0.0.0.0:8000 app:app
```

# The internals

## Database

The milestone is support:

- Postgres [x]
- MySQL/MariDB
- SQLite
- Redshift

DB connection and inspection is done using SQLAlchemy

SQL queries are made with: https://github.com/kayak/pypika

### Special queries

These queries are made to reduce the overhead in some cases such as a bulk delete where we validate if the ids provided are in our db first

see: `chillapi.database.repository._MAGIC_QUERIES`

# Endpoints

Based on the config file.

Extends from: `chillapi.swagger.http.AutomaticResource`

## Table type

Automatically maps all the table and exposes all the columns.

Exclusion by `excluded_fields` config

As far this a direct map to the columns, the POST/PUT endpoints will require as request body these columns, and the response body will show that columns.

DELETE and POST automatically attach the id the url, this field is mapper ti the `id_field` config

Same way bulk operations will map the `id_field` config to the correspondent field in the request body.

## SQL Type

This type of endpoint in the simplest case will throw a response with a json that contains the result of the SQl specified.

In addition, you can use placeholders in your query and specify the proper swagger schema in the config.

## Template type

Works in the same way that the SQL type, but you can specify a path to a template (larger sqls)

# setup development

```shell
cd $PROJECT_DIR
```

```shell
docker-compose up
```

```shell
make run_dev
# or install by yourself the venv etc. You will need to have psycopg binary installed
```

See `Makefile`

# Other options

https://github.com/dbohdan/automatic-api
