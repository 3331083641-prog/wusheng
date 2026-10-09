from pathlib import Path
import os
import uuid
from datetime import datetime, timezone
from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, Session

ROOT = Path(__file__).resolve().parents[1]
DATA = Path(os.getenv('WUSHENG_DATA_DIR', str(ROOT / 'data'))).resolve()
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


def migrate_schema(target_engine):
    """Additive migration: preserve existing archives and all business values."""
    from sqlalchemy import inspect, text
    additions = {
        # Optional provenance only; existing business records remain unchanged.
        'item_images': {'originalFilename': "TEXT DEFAULT ''", 'storedFilename': "TEXT DEFAULT ''", 'mimeType': "TEXT DEFAULT ''", 'fileSize': 'INTEGER DEFAULT 0', 'sha256': "TEXT DEFAULT ''", 'createdAt': "TEXT DEFAULT ''"},
        'documents': {'originalFilename': "TEXT DEFAULT ''", 'storedFilename': "TEXT DEFAULT ''", 'mimeType': "TEXT DEFAULT 'application/pdf'", 'fileSize': 'INTEGER DEFAULT 0', 'sha256': "TEXT DEFAULT ''", 'pageCount': 'INTEGER', 'updatedAt': "TEXT DEFAULT ''", 'textStatus': "TEXT DEFAULT 'needs_ocr'", 'textSource': "TEXT DEFAULT 'none'", 'ocrPageCount': 'INTEGER DEFAULT 0', 'ocrError': "TEXT DEFAULT ''"},
        'consumables': {'createdAt': "TEXT DEFAULT ''", 'updatedAt': "TEXT DEFAULT ''"},
        'recognition_sessions': {'draftId': 'TEXT'},
        'share_links': {'expiresAt': 'TEXT', 'options': 'JSON'},
    }
    for table in ('item_images', 'documents'):
        additions[table]['assetMetadata'] = 'JSON'
    with target_engine.begin() as connection:
        for table, fields in additions.items():
            if not inspect(connection).has_table(table):
                continue  # create_all creates new tables; old partial migration fixtures are valid.
            existing = {c['name'] for c in inspect(connection).get_columns(table)}
            for name, definition in fields.items():
                if name not in existing:
                    connection.execute(text(f'ALTER TABLE {table} ADD COLUMN "{name}" {definition}'))
        for table in ['item_images', 'documents', 'consumables']:
            for field in ['createdAt', 'updatedAt']:
                if field in {c['name'] for c in inspect(connection).get_columns(table)}:
                    connection.execute(text(f'UPDATE {table} SET "{field}"=:now WHERE "{field}" IS NULL OR "{field}"=\'\''), {'now': timestamp()})
        if 'extractedText' in {c['name'] for c in inspect(connection).get_columns('documents')}:
            connection.execute(text("UPDATE documents SET textStatus='text_ready', textSource='pdf_text' WHERE length(trim(extractedText))>0 AND textSource='none'"))
        # Type is stored as TEXT; extending the accepted enum preserves old rows.


def get_db():
    with Session(engine) as session:
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
