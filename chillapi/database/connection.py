import os
from typing import Dict

from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import scoped_session, sessionmaker

TYPE_RELATIONAL = "relational"
TYPE_DOCUMENT = "document"
TYPE_FILE = "file"


def create_db_toolbox(database_dict: dict) -> Dict:
    """

    :param environment: dict:
    :param schemas: str:  (Default value = None)

    """
    type = TYPE_RELATIONAL
    if database_dict["dsn"].startswith("$"):
        database_dict["dsn"] = os.getenv(database_dict["dsn"].replace("$", "", 1))

    db_url = database_dict["dsn"]
    connect_args = {}

    if db_url.__contains__("postgresql"):
        connect_args = {"options": f"-csearch_path={database_dict['schema']}"}
    # if db_url.__contains__("sqlite"):
    #     @event.listens_for(Engine, "connect")
    #     def set_sqlite_pragma(dbapi_connection, connection_record):
    #         cursor = dbapi_connection.cursor()
    #         cursor.execute("PRAGMA synchronous  = 3")
    #         cursor.execute('PRAGMA journal_mode = MEMORY')
    #         cursor.execute('PRAGMA foreign_keys = 1')
    #         cursor.execute('PRAGMA read_uncommitted = 1')
    #         cursor.execute('PRAGMA query_only = 0')
    #         # cursor.close()

    engine = create_engine(db_url, encoding="utf8", connect_args=connect_args)

    SessionLocal = scoped_session(sessionmaker(bind=engine, autocommit=True, autoflush=True))
    db = SessionLocal()

    try:
        return {
            "session": db,
            "inspector": inspect(engine),
            "type": type,
        }
    finally:
        # if db_url.__contains__("sqlite"):
        #     engine.dispose()
        db.close()
