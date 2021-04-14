from sqlalchemy.engine import Inspector
from typing import Tuple

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy import inspect

from sqlalchemy.orm.scoping import ScopedSession


def create_db(db_url: str, schemas: str) -> Tuple[ScopedSession, Inspector]:
    engine = create_engine(
        db_url,
        encoding='utf8',
        connect_args={'options': f'-csearch_path={schemas}'}
    )

    SessionLocal = scoped_session(sessionmaker(bind=engine))
    db = SessionLocal()
    try:
        return db, inspect(engine)
    finally:
        db.close()
