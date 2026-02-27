from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import sqlite3
import os
from datetime import datetime

router = APIRouter()

DB_PATH = os.path.join(os.path.dirname(__file__), "../knowledge/brainforce.db")

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

@router.post("/save/")
def save_memory(data: dict):
    conn = get_db()
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS memory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            role TEXT,
            message TEXT,
            timestamp TEXT
        )
    """)
    c.execute(
        "INSERT INTO memory (role, message, timestamp) VALUES (?, ?, ?)",
        (data.get("role", ""), data.get("message", ""), datetime.utcnow().isoformat())
    )
    conn.commit()
    return {"status": "saved"}

@router.get("/all/")
def get_all_memory():
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM memory ORDER BY id DESC LIMIT 200")
    rows = c.fetchall()
    return [dict(row) for row in rows]
