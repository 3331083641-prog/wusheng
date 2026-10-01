from pathlib import Path
import os
import uuid
from datetime import datetime, timezone
from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, Session

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data'
UPLOADS = DATA / 'uploads'
UPLOADS.mkdir(parents=True, exist_ok=True)


class Base(DeclarativeBase):
    pass


def uid():
    return str(uuid.uuid4())


def timestamp():
    return datetime.now(timezone.utc).isoformat()


def make_engine(url):
    result = create_engine(url, connect_args={'check_same_thread': False})

    @event.listens_for(result, 'connect')
    def foreign_keys(connection, _):
        connection.execute('PRAGMA foreign_keys=ON')
        connection.execute('PRAGMA busy_timeout=5000')

    return result


engine = make_engine(os.getenv('WUSHENG_DB_URL', f'sqlite:///{DATA / "wusheng.db"}'))


def get_db():
    with Session(engine) as session:
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
