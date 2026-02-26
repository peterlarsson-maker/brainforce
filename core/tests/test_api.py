import os

from fastapi.testclient import TestClient


def test_openai_requires_session_id(tmp_path, monkeypatch):
    import core.database as database
    db_file = tmp_path / "test_api.db"
    monkeypatch.setattr(database, "DB_PATH", str(db_file))
    database.init_db()

    from core.main import app
    client = TestClient(app)

    # Missing X-Session-Id header -> 400
    r = client.post("/api/openai/", json={"prompt": "hello"})
    assert r.status_code == 400
    assert "X-Session-Id" in r.json().get("detail", "")


def test_openai_mock_includes_memory_and_persists_reply(tmp_path, monkeypatch):
    import core.database as database
    db_file = tmp_path / "test_api_mock.db"
    monkeypatch.setattr(database, "DB_PATH", str(db_file))
    database.init_db()

    # Enable mock mode so we don't call external OpenAI
    monkeypatch.setenv("MOCK_MODE", "1")

    from core.main import app
    client = TestClient(app)

    # prepare memory for two sessions (s1 and s2)
    s1 = "session-1"
    s2 = "session-2"
    # save some history for s1
    client.post("/memory/save/", json={"session_id": s1, "role": "user", "message": "m1"})
    client.post("/memory/save/", json={"session_id": s1, "role": "assistant", "message": "a1"})
    # save an entry for s2 to ensure isolation
    client.post("/memory/save/", json={"session_id": s2, "role": "user", "message": "other"})

    headers = {"X-Session-Id": s1}
    prompt = "please respond"
    r = client.post("/api/openai/", json={"prompt": prompt}, headers=headers)
    assert r.status_code == 200
    body = r.json()
    assert body.get("session_id") == s1
    # messages should include the stored history for s1, oldest-first, and the prompt as last message
    messages = body.get("messages")
    assert isinstance(messages, list)
    assert messages[-1]["content"] == prompt
    # earlier messages should contain m1 and a1 in order
    contents = [m["content"] for m in messages[:-1]]
    assert "m1" in contents and "a1" in contents

    # The assistant reply should have been persisted to memory for s1
    mem = client.get(f"/memory/session/{s1}/").json()
    # find any assistant messages
    assistants = [m for m in mem if m.get("role") == "assistant"]
    assert any("MOCK_REPLY" in a.get("message", "") for a in assistants)

    # The user prompt should also have been persisted to memory for s1
    assert any(m.get("role") == "user" and m.get("message") == prompt for m in mem)

    # ensure s2 memory was not modified (no assistant replies added)
    mem2 = client.get(f"/memory/session/{s2}/").json()
    assert all(m.get("role") != "assistant" for m in mem2)


def test_history_trimming_with_large_history(tmp_path, monkeypatch):
    import core.database as database
    db_file = tmp_path / "test_api_trim.db"
    monkeypatch.setattr(database, "DB_PATH", str(db_file))
    database.init_db()

    # Enable mock mode
    monkeypatch.setenv("MOCK_MODE", "1")
    # Ensure deterministic token budget for the test
    monkeypatch.setenv("MEMORY_TOKEN_BUDGET", "3000")

    from core.main import app
    client = TestClient(app)

    s = "trim-session"

    # Create a large history: many messages of ~200 chars (~50 tokens each)
    long_msg = "x" * 200
    total_msgs = 80
    for i in range(total_msgs):
        client.post("/memory/save/", json={"session_id": s, "role": "user", "message": f"{i}-{long_msg}"})

    headers = {"X-Session-Id": s}
    prompt = "final prompt to include"
    r = client.post("/api/openai/", json={"prompt": prompt}, headers=headers)
    assert r.status_code == 200
    body = r.json()
    messages = body.get("messages")
    assert isinstance(messages, list)
    # Last message must be the prompt
    assert messages[-1]["content"] == prompt

    # Verify trimming: estimated tokens of included messages should not exceed budget
    def est(s: str) -> int:
        return max(1, (len(s) + 3) // 4)

    total_est = sum(est(m["content"]) for m in messages)
    assert total_est <= 3000

    # Ensure we didn't include the entire original history (trimming occurred)
    assert len(messages) < total_msgs + 1
