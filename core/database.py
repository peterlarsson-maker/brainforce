"""Database helpers for BrainForce.

Provides get_db() and a simple init_db() to ensure schema exists.
"""
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "../knowledge/brainforce.db")


def ensure_db_dir():
    d = os.path.dirname(DB_PATH)
    if d and not os.path.exists(d):
        os.makedirs(d, exist_ok=True)


def get_db():
    ensure_db_dir()
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Initialize DB schema for memory and users (safe to call multiple times)."""
    conn = get_db()
    c = conn.cursor()
    # user table used for authentication
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password_hash TEXT,
            role TEXT,
            created_at TEXT
        )
    """)
    # memory table now tracks user_id so that sessions are scoped
    c.execute("""
        CREATE TABLE IF NOT EXISTS memory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT,
            user_id INTEGER,
            role TEXT,
            message TEXT,
            timestamp TEXT,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    """)
    # index to speed lookups by session and user
    c.execute("CREATE INDEX IF NOT EXISTS idx_memory_session ON memory(session_id)")
    conn.commit()
    conn.close()
