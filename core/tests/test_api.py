import os
from datetime import datetime, timedelta

from fastapi.testclient import TestClient

from core.auth import hash_password



# explicit tests for authentication

def test_login_endpoint(tmp_path, monkeypatch):
    import core.database as database
    db_file = tmp_path / "test_login.db"
    monkeypatch.setattr(database, "DB_PATH", str(db_file))
    # authentication requires a secret
    monkeypatch.setenv("JWT_SECRET", "testsecret")
    database.init_db()
    from core.main import app
    client = TestClient(app)

    # create a user directly in the database
    from core.database import get_db
    conn = get_db()
    c = conn.cursor()
    c.execute(
        "INSERT INTO users (username, password_hash, role, created_at) VALUES (?, ?, ?, ?)",
        ("alice", hash_password("wordpass"), "admin", datetime.utcnow().isoformat()),
    )
    conn.commit()

    # valid credentials return token
    r = client.post("/auth/login", json={"username": "alice", "password": "wordpass"})
    assert r.status_code == 200
    data = r.json()
    assert "access_token" in data and data["token_type"] == "bearer"

    # bad credentials give 401
    r2 = client.post("/auth/login", json={"username": "alice", "password": "wrong"})
    assert r2.status_code == 401


def create_test_user(client: TestClient, username: str = "user", password: str = "secret") -> str:
    """Helper that seeds a user into the test database and returns a valid JWT."""
    # insert directly into sqlite since no user creation endpoint exists yet
    from core.database import get_db
    conn = get_db()
    c = conn.cursor()
    c.execute(
        "INSERT INTO users (username, password_hash, role, created_at) VALUES (?, ?, ?, ?)",
        (username, hash_password(password), "user", datetime.utcnow().isoformat()),
    )
    conn.commit()
    # call login endpoint to obtain token
    resp = client.post("/auth/login", json={"username": username, "password": password})
    assert resp.status_code == 200, "login failed in test helper"
    return resp.json()["access_token"]


def test_openai_requires_session_id(tmp_path, monkeypatch):
    import core.database as database
    db_file = tmp_path / "test_api.db"
    monkeypatch.setattr(database, "DB_PATH", str(db_file))
    database.init_db()

    from core.main import app
    client = TestClient(app)

    # ensure JWT_SECRET is defined for token creation
    monkeypatch.setenv("JWT_SECRET", "anothersecret")

    # create a test user and get token
    token = create_test_user(client)
    headers = {"Authorization": f"Bearer {token}"}

    # Missing X-Session-Id header -> 400
    r = client.post("/api/openai/", json={"prompt": "hello"}, headers=headers)
    assert r.status_code == 400
    assert "X-Session-Id" in r.json().get("detail", "")


def test_protected_endpoint_requires_auth(tmp_path, monkeypatch):
    """Calling the OpenAI proxy without a bearer token should be rejected."""
    import core.database as database
    db_file = tmp_path / "test_prot.db"
    monkeypatch.setattr(database, "DB_PATH", str(db_file))
    database.init_db()
    monkeypatch.setenv("JWT_SECRET", "sig")
    from core.main import app
    client = TestClient(app)

    r = client.post("/api/openai/", json={"prompt": "hi"}, headers={})
    assert r.status_code == 401


def test_invalid_token_is_rejected(tmp_path, monkeypatch):
    """Providing an invalid bearer token yields 401, same as missing one."""
    import core.database as database
    db_file = tmp_path / "test_badtok.db"
    monkeypatch.setattr(database, "DB_PATH", str(db_file))
    monkeypatch.setenv("JWT_SECRET", "foo")
    database.init_db()
    from core.main import app
    client = TestClient(app)

    headers = {"Authorization": "Bearer notavalidtoken"}
    r = client.post("/api/openai/", json={"prompt": "x"}, headers=headers)
    assert r.status_code == 401


def test_token_with_wrong_algorithm_rejected(tmp_path, monkeypatch):
    """Token with alg != HS256 should be rejected."""
    import core.database as database
    db_file = tmp_path / "test_alg.db"
    monkeypatch.setattr(database, "DB_PATH", str(db_file))
    monkeypatch.setenv("JWT_SECRET", "secret")
    database.init_db()
    
    from core.main import app
    client = TestClient(app)
    
    # Create a token manually with wrong algorithm
    from core.auth import _b64url_encode, _get_jwt_secret
    import hmac
    import hashlib
    import json
    
    header = {"alg": "HS512", "typ": "JWT"}  # Wrong algorithm
    payload = {"user_id": 1, "role": "user", "exp": int((datetime.utcnow() + timedelta(hours=1)).timestamp())}
    
    header_b = _b64url_encode(json.dumps(header).encode())
    payload_b = _b64url_encode(json.dumps(payload).encode())
    secret = _get_jwt_secret().encode()
    sig = hmac.new(secret, f"{header_b}.{payload_b}".encode(), hashlib.sha256).digest()
    sig_b = _b64url_encode(sig)
    bad_token = f"{header_b}.{payload_b}.{sig_b}"
    
    headers = {"Authorization": f"Bearer {bad_token}"}
    r = client.post("/api/openai/", json={"prompt": "x"}, headers=headers)
    assert r.status_code == 401


def test_token_missing_user_id_rejected(tmp_path, monkeypatch):
    """Token without user_id claim should be rejected."""
    import core.database as database
    db_file = tmp_path / "test_no_uid.db"
    monkeypatch.setattr(database, "DB_PATH", str(db_file))
    monkeypatch.setenv("JWT_SECRET", "secret")
    database.init_db()
    
    from core.main import app
    client = TestClient(app)
    
    # Create a token manually without user_id
    from core.auth import _b64url_encode, _get_jwt_secret
    import hmac
    import hashlib
    import json
    
    header = {"alg": "HS256", "typ": "JWT"}
    payload = {"role": "user", "exp": int((datetime.utcnow() + timedelta(hours=1)).timestamp())}  # Missing user_id
    
    header_b = _b64url_encode(json.dumps(header).encode())
    payload_b = _b64url_encode(json.dumps(payload).encode())
    secret = _get_jwt_secret().encode()
    sig = hmac.new(secret, f"{header_b}.{payload_b}".encode(), hashlib.sha256).digest()
    sig_b = _b64url_encode(sig)
    bad_token = f"{header_b}.{payload_b}.{sig_b}"
    
    headers = {"Authorization": f"Bearer {bad_token}"}
    r = client.post("/api/openai/", json={"prompt": "x"}, headers=headers)
    assert r.status_code == 401


def test_token_missing_role_rejected(tmp_path, monkeypatch):
    """Token without role claim should be rejected."""
    import core.database as database
    db_file = tmp_path / "test_no_role.db"
    monkeypatch.setattr(database, "DB_PATH", str(db_file))
    monkeypatch.setenv("JWT_SECRET", "secret")
    database.init_db()
    
    from core.main import app
    client = TestClient(app)
    
    # Create a token manually without role
    from core.auth import _b64url_encode, _get_jwt_secret
    import hmac
    import hashlib
    import json
    
    header = {"alg": "HS256", "typ": "JWT"}
    payload = {"user_id": 1, "exp": int((datetime.utcnow() + timedelta(hours=1)).timestamp())}  # Missing role
    
    header_b = _b64url_encode(json.dumps(header).encode())
    payload_b = _b64url_encode(json.dumps(payload).encode())
    secret = _get_jwt_secret().encode()
    sig = hmac.new(secret, f"{header_b}.{payload_b}".encode(), hashlib.sha256).digest()
    sig_b = _b64url_encode(sig)
    bad_token = f"{header_b}.{payload_b}.{sig_b}"
    
    headers = {"Authorization": f"Bearer {bad_token}"}
    r = client.post("/api/openai/", json={"prompt": "x"}, headers=headers)
    assert r.status_code == 401


def test_token_missing_exp_rejected(tmp_path, monkeypatch):
    """Token without exp claim should be rejected."""
    import core.database as database
    db_file = tmp_path / "test_no_exp.db"
    monkeypatch.setattr(database, "DB_PATH", str(db_file))
    monkeypatch.setenv("JWT_SECRET", "secret")
    database.init_db()
    
    from core.main import app
    client = TestClient(app)
    
    # Create a token manually without exp
    from core.auth import _b64url_encode, _get_jwt_secret
    import hmac
    import hashlib
    import json
    
    header = {"alg": "HS256", "typ": "JWT"}
    payload = {"user_id": 1, "role": "user"}  # Missing exp
    
    header_b = _b64url_encode(json.dumps(header).encode())
    payload_b = _b64url_encode(json.dumps(payload).encode())
    secret = _get_jwt_secret().encode()
    sig = hmac.new(secret, f"{header_b}.{payload_b}".encode(), hashlib.sha256).digest()
    sig_b = _b64url_encode(sig)
    bad_token = f"{header_b}.{payload_b}.{sig_b}"
    
    headers = {"Authorization": f"Bearer {bad_token}"}
    r = client.post("/api/openai/", json={"prompt": "x"}, headers=headers)
    assert r.status_code == 401


def test_register_creates_user_as_admin(tmp_path, monkeypatch):
    """Admin can successfully register a new user."""
    import core.database as database

    db_file = tmp_path / "test_reg.db"
    monkeypatch.setattr(database, "DB_PATH", str(db_file))
    monkeypatch.setenv("JWT_SECRET", "sec")
    database.init_db()
    from core.main import app

    client = TestClient(app)

    # seed an admin user
    from core.database import get_db

    conn = get_db()
    c = conn.cursor()
    c.execute(
        "INSERT INTO users (username, password_hash, role, created_at) VALUES (?, ?, ?, ?)",
        ("admin1", hash_password("adminpass"), "admin", datetime.utcnow().isoformat()),
    )
    conn.commit()

    # log in as admin
    r_login = client.post("/auth/login", json={"username": "admin1", "password": "adminpass"})
    assert r_login.status_code == 200
    admin_token = r_login.json()["access_token"]
    headers = {"Authorization": f"Bearer {admin_token}"}

    # register a new user
    r = client.post("/auth/register", json={"username": "newuser", "password": "newpass"}, headers=headers)
    assert r.status_code == 201
    data = r.json()
    assert data["username"] == "newuser"
    assert isinstance(data["id"], int)
    assert data["id"] > 0


def test_register_rejects_duplicate_username(tmp_path, monkeypatch):
    """Registration with a duplicate username returns 400."""
    import core.database as database

    db_file = tmp_path / "test_dup.db"
    monkeypatch.setattr(database, "DB_PATH", str(db_file))
    monkeypatch.setenv("JWT_SECRET", "sec2")
    database.init_db()
    from core.main import app

    client = TestClient(app)

    # seed an admin and a regular user
    from core.database import get_db

    conn = get_db()
    c = conn.cursor()
    c.execute(
        "INSERT INTO users (username, password_hash, role, created_at) VALUES (?, ?, ?, ?)",
        ("admin", hash_password("pass"), "admin", datetime.utcnow().isoformat()),
    )
    c.execute(
        "INSERT INTO users (username, password_hash, role, created_at) VALUES (?, ?, ?, ?)",
        ("existing", hash_password("pass"), "user", datetime.utcnow().isoformat()),
    )
    conn.commit()

    # log in as admin
    r_login = client.post("/auth/login", json={"username": "admin", "password": "pass"})
    admin_token = r_login.json()["access_token"]
    headers = {"Authorization": f"Bearer {admin_token}"}

    # try to register with the existing username
    r = client.post("/auth/register", json={"username": "existing", "password": "newpass"}, headers=headers)
    assert r.status_code == 400
    assert "already exists" in r.json().get("detail", "")


def test_register_non_admin_forbidden(tmp_path, monkeypatch):
    """Non-admin user cannot register new users."""
    import core.database as database

    db_file = tmp_path / "test_nonadmin.db"
    monkeypatch.setattr(database, "DB_PATH", str(db_file))
    monkeypatch.setenv("JWT_SECRET", "sec3")
    database.init_db()
    from core.main import app

    client = TestClient(app)

    # seed a regular user (non-admin)
    from core.database import get_db

    conn = get_db()
    c = conn.cursor()
    c.execute(
        "INSERT INTO users (username, password_hash, role, created_at) VALUES (?, ?, ?, ?)",
        ("normaluser", hash_password("pass"), "user", datetime.utcnow().isoformat()),
    )
    conn.commit()

    # log in as regular user
    r_login = client.post("/auth/login", json={"username": "normaluser", "password": "pass"})
    user_token = r_login.json()["access_token"]
    headers = {"Authorization": f"Bearer {user_token}"}

    # try to register a new user (should fail)
    r = client.post("/auth/register", json={"username": "another", "password": "pass"}, headers=headers)
    assert r.status_code == 403
    assert "admin" in r.json().get("detail", "").lower()


def test_session_id_cannot_cross_users(tmp_path, monkeypatch):
    """A session_id already used by one user may not be reused by another."""
    import core.database as database
    db_file = tmp_path / "test_one.db"
    monkeypatch.setattr(database, "DB_PATH", str(db_file))
    monkeypatch.setenv("JWT_SECRET", "s3cret")
    database.init_db()
    from core.main import app
    client = TestClient(app)

    # create two users
    u1 = create_test_user(client, username="u1", password="pw1")
    u2 = create_test_user(client, username="u2", password="pw2")
    h1 = {"Authorization": f"Bearer {u1}"}
    h2 = {"Authorization": f"Bearer {u2}"}

    # user1 starts a session
    r1 = client.post("/memory/save/", json={"session_id": "sess", "role": "user", "message": "msg"}, headers=h1)
    assert r1.status_code == 200

    # user2 tries to use the same session id and should get a 400
    r2 = client.post("/memory/save/", json={"session_id": "sess", "role": "user", "message": "other"}, headers=h2)
    assert r2.status_code == 400
    assert "already used" in r2.json().get("detail", "")


def test_openai_mock_includes_memory_and_persists_reply(tmp_path, monkeypatch):
    import core.database as database
    db_file = tmp_path / "test_api_mock.db"
    monkeypatch.setattr(database, "DB_PATH", str(db_file))
    database.init_db()

    # Enable mock mode so we don't call external OpenAI
    monkeypatch.setenv("MOCK_MODE", "1")

    from core.main import app
    client = TestClient(app)

    # make sure a secret exists before logging in
    monkeypatch.setenv("JWT_SECRET", "dummy")
    # create a user and get token
    token = create_test_user(client)
    auth_headers = {"Authorization": f"Bearer {token}"}

    # prepare memory for two sessions (s1 and s2) associated with the same user
    s1 = "session-1"
    s2 = "session-2"
    # save some history for s1
    client.post("/memory/save/", json={"session_id": s1, "role": "user", "message": "m1"}, headers=auth_headers)
    client.post("/memory/save/", json={"session_id": s1, "role": "assistant", "message": "a1"}, headers=auth_headers)
    # save an entry for s2 to ensure isolation
    client.post("/memory/save/", json={"session_id": s2, "role": "user", "message": "other"}, headers=auth_headers)

    headers = {"X-Session-Id": s1, **auth_headers}
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
    mem = client.get(f"/memory/session/{s1}/", headers=auth_headers).json()
    # find any assistant messages
    assistants = [m for m in mem if m.get("role") == "assistant"]
    assert any("MOCK_REPLY" in a.get("message", "") for a in assistants)

    # The user prompt should also have been persisted to memory for s1
    assert any(m.get("role") == "user" and m.get("message") == prompt for m in mem)

    # ensure s2 memory was not modified (no assistant replies added)
    mem2 = client.get(f"/memory/session/{s2}/", headers=auth_headers).json()
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

    # make sure a secret is available
    monkeypatch.setenv("JWT_SECRET", "thirdsecret")

    # create and login user
    token = create_test_user(client)
    auth_headers = {"Authorization": f"Bearer {token}"}

    s = "trim-session"

    # Create a large history: many messages of ~200 chars (~50 tokens each)
    long_msg = "x" * 200
    total_msgs = 80
    for i in range(total_msgs):
        client.post(
            "/memory/save/",
            json={"session_id": s, "role": "user", "message": f"{i}-{long_msg}"},
            headers=auth_headers,
        )

    headers = {"X-Session-Id": s, **auth_headers}
    prompt = "final prompt to include"
    r = client.post("/api/openai/", json={"prompt": prompt}, headers=headers)
    assert r.status_code == 200
    body = r.json()
    messages = body.get("messages")
    assert isinstance(messages, list)
    # Last message must be the prompt
    assert messages[-1]["content"] == prompt

    # confirm the prompt was actually written to memory
    mem_after = client.get(f"/memory/session/{s}/", headers=auth_headers).json()
    assert any(m.get("role") == "user" and m.get("message") == prompt for m in mem_after)

    # Verify trimming: estimated tokens of included messages should not exceed budget
    def est(s: str) -> int:
        return max(1, (len(s) + 3) // 4)

    total_est = sum(est(m["content"]) for m in messages)
    assert total_est <= 3000

    # Ensure we didn't include the entire original history (trimming occurred)
    assert len(messages) < total_msgs + 1


def test_login_rate_limit_5_attempts_allowed(tmp_path, monkeypatch):
    """5 failed attempts should be allowed without 429."""
    import core.database as database
    db_file = tmp_path / "test_rate_limit.db"
    monkeypatch.setattr(database, "DB_PATH", str(db_file))
    monkeypatch.setenv("JWT_SECRET", "testsecret")
    database.init_db()
    
    from core.main import app
    from core.auth import _login_attempts
    # Reset rate limiter state for clean test
    _login_attempts.clear()
    
    client = TestClient(app)
    
    # Create a user
    from core.database import get_db
    conn = get_db()
    c = conn.cursor()
    c.execute(
        "INSERT INTO users (username, password_hash, role, created_at) VALUES (?, ?, ?, ?)",
        ("testuser", hash_password("correctpass"), "user", datetime.utcnow().isoformat()),
    )
    conn.commit()
    conn.close()
    
    # 5 failed attempts should all return 401 (not 429)
    for attempt in range(1, 6):
        r = client.post("/auth/login", json={"username": "testuser", "password": "wrongpass"})
        assert r.status_code == 401, f"Attempt {attempt} should return 401"


def test_login_rate_limit_6th_attempt_returns_429(tmp_path, monkeypatch):
    """6th failed attempt should return 429."""
    import core.database as database
    db_file = tmp_path / "test_rate_limit_429.db"
    monkeypatch.setattr(database, "DB_PATH", str(db_file))
    monkeypatch.setenv("JWT_SECRET", "testsecret")
    database.init_db()
    
    from core.main import app
    from core.auth import _login_attempts
    # Reset rate limiter state for clean test
    _login_attempts.clear()
    
    client = TestClient(app)
    
    # Create a user
    from core.database import get_db
    conn = get_db()
    c = conn.cursor()
    c.execute(
        "INSERT INTO users (username, password_hash, role, created_at) VALUES (?, ?, ?, ?)",
        ("testuser", hash_password("correctpass"), "user", datetime.utcnow().isoformat()),
    )
    conn.commit()
    conn.close()
    
    # 5 failed attempts
    for attempt in range(1, 6):
        r = client.post("/auth/login", json={"username": "testuser", "password": "wrongpass"})
        assert r.status_code == 401
    
    # 6th attempt should return 429
    r = client.post("/auth/login", json={"username": "testuser", "password": "wrongpass"})
    assert r.status_code == 429
    assert "Too many failed login attempts" in r.json().get("detail", "")


def test_login_rate_limit_reset_on_success(tmp_path, monkeypatch):
    """Successful login should reset the attempt counter."""
    import core.database as database
    db_file = tmp_path / "test_rate_limit_reset.db"
    monkeypatch.setattr(database, "DB_PATH", str(db_file))
    monkeypatch.setenv("JWT_SECRET", "testsecret")
    database.init_db()
    
    from core.main import app
    from core.auth import _login_attempts
    # Reset rate limiter state for clean test
    _login_attempts.clear()
    
    client = TestClient(app)
    
    # Create a user
    from core.database import get_db
    conn = get_db()
    c = conn.cursor()
    c.execute(
        "INSERT INTO users (username, password_hash, role, created_at) VALUES (?, ?, ?, ?)",
        ("testuser", hash_password("correctpass"), "user", datetime.utcnow().isoformat()),
    )
    conn.commit()
    conn.close()
    
    # 3 failed attempts
    for attempt in range(1, 4):
        r = client.post("/auth/login", json={"username": "testuser", "password": "wrongpass"})
        assert r.status_code == 401
    
    # Successful login (counter should reset)
    r = client.post("/auth/login", json={"username": "testuser", "password": "correctpass"})
    assert r.status_code == 200
    assert "access_token" in r.json()
    
    # After reset, we should be able to make 5 more failed attempts without hitting 429
    for attempt in range(1, 6):
        r = client.post("/auth/login", json={"username": "testuser", "password": "wrongpass"})
        assert r.status_code == 401, f"Attempt {attempt} after reset should return 401"
    
    # 6th attempt should hit rate limit again
    r = client.post("/auth/login", json={"username": "testuser", "password": "wrongpass"})
    assert r.status_code == 429


