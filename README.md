# ChillApi

## Motivation

This project was born to increase the speed of delivery and development of APIs.

The premise is simple, not all roles can feel comfortable swimming in a sea of indented code, however they do feel comfortable in SQL languages. And those who do feel comfortable programming may prefer to use a tool that configures and propagates information than extending an ORM, routes, forms, etc; thus being able to spend more time on other types of tasks.

The connection and execution of queries is done in raw, that is, there is no ORM involved.

The implementation of this framework is on Flask using a series of additional libraries and adopting others to satisfy the requirements of the same.

# The internals

## Database

The milestone is support:

- Postgres
- MySQL/MariDB
- SQLite
- Redshift

The introspection is done using: https://github.com/djrobstep/schemainspect

SQL queries are made with: https://github.com/kayak/pypika

### Special queries

This queries are made to reduce the overhead in some cases such as a bulk delete where we validate if the ids provided are in our db first

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

# setup

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

# Other options

https://github.com/dbohdan/automatic-api
