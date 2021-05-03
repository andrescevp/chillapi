from typing import Tuple

from sqlalchemy import create_engine, inspect
from sqlalchemy.engine import Inspector
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.orm.scoping import ScopedSession


def create_db(environment: dict, schemas: str = None) -> Tuple[ScopedSession, Inspector]:
    db_url = environment["__CHILLAPI_DB_DSN__"]
    connect_args = {}

    if db_url.__contains__("postgresql"):
        connect_args = {"options": f"-csearch_path={schemas}"}
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
        return db, inspect(engine)
    finally:
        # if db_url.__contains__("sqlite"):
        #     engine.dispose()
        db.close()
