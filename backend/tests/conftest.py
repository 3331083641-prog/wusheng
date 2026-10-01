import pytest
from sqlalchemy.orm import Session
from fastapi.testclient import TestClient
from backend.database import Base,make_engine,get_db
from backend import main


@pytest.fixture
def client(tmp_path,monkeypatch):
    engine=make_engine(f'sqlite:///{tmp_path / "test.db"}')
    monkeypatch.setattr(main,'engine',engine)
    Base.metadata.create_all(engine)
    def session():
        with Session(engine) as db:
            try:
                yield db
                db.commit()
            except Exception:
                db.rollback()
                raise
    main.app.dependency_overrides[get_db]=session
    with TestClient(main.app) as c:yield c
    main.app.dependency_overrides.clear()
    engine.dispose()
