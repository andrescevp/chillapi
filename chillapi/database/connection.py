from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
import os

from sqlalchemy.orm.scoping import ScopedSession
from chillapi.app.config import api_config, _get_db_url

SQLALCHEMY_DATABASE_URL = os.getenv('CODEBOOK_DB_URL')
SQLALCHEMY_DATABASE_SCHEMA = 'public'  # 'schema1,schema2,public'

engine = create_engine(
    _get_db_url(api_config),
    encoding='utf8',
    connect_args={'options': f'-csearch_path={SQLALCHEMY_DATABASE_SCHEMA}'}
)

SessionLocal = scoped_session(sessionmaker(bind=engine))


def get_db() -> ScopedSession:
    db = SessionLocal()
    try:
        return db
    finally:
        db.close()


db = get_db()
