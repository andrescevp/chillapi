DB_DIALECT_POSTGRES = 'postgres'
DB_DIALECT_SQLITE = 'sqlite'

_ALLOWED_DRIVERS = {
    'psycopg2': DB_DIALECT_POSTGRES,
    'sqlite3.dbapi2': DB_DIALECT_SQLITE,
}
