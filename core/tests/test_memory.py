import os
import importlib

from fastapi.testclient import TestClient


def test_save_and_get_memory(tmp_path, monkeypatch):
    # Point DB to a temporary file and initialize schema
    import core.database as database
    db_file = tmp_path / "test.db"
    monkeypatch.setattr(database, "DB_PATH", str(db_file))
    database.init_db()

    # Import app after DB_PATH is set (core.main may already be imported elsewhere)
    from core.main import app
    client = TestClient(app)

    # Missing session_id in body should result in validation error (422)
    r = client.post("/memory/save/", json={"role": "user", "message": "hi"})
    assert r.status_code == 422

    # Correct save with session_id
    r = client.post(
        "/memory/save/",
        json={"session_id": "s1", "role": "user", "message": "hello"},
    )
    assert r.status_code == 200
    assert r.json().get("status") == "saved"

    # Retrieve by session
    r = client.get("/memory/session/s1/")
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, list) and any(item.get("message") == "hello" for item in data)
