from typing import Tuple

from sqlalchemy import create_engine, inspect
from sqlalchemy.engine import Inspector
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.orm.scoping import ScopedSession


def create_db(db_url: str, schemas: str = None) -> Tuple[ScopedSession, Inspector]:
    connect_args = {}

    if db_url.__contains__("postgresql"):
        connect_args = {"options": f"-csearch_path={schemas}"}

    engine = create_engine(db_url, encoding="utf8", connect_args=connect_args)

    SessionLocal = scoped_session(sessionmaker(bind=engine, autocommit=True, autoflush=True))
    db = SessionLocal()

    try:
        return db, inspect(engine)
    finally:
        # if db_url.__contains__("sqlite"):
        #     engine.dispose()
        db.close()
