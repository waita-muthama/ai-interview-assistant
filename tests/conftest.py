import pytest
from fastapi.testclient import TestClient
from server import db
from server.main import app


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(db, 'DATA_DIR', tmp_path)
    monkeypatch.setattr(db, 'DB_PATH', tmp_path / 'test.sqlite3')
    with TestClient(app) as c:
        yield c
