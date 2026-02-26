from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, timezone
from core.database import get_db

router = APIRouter()


class MemorySave(BaseModel):
    session_id: str
    role: Optional[str] = ""
    message: str


@router.post("/save/")
def save_memory(data: MemorySave):
    """Save a memory entry tied to a session_id."""
    if not data.session_id:
        raise HTTPException(status_code=400, detail="session_id is required")

    conn = get_db()
    c = conn.cursor()
    # Ensure schema includes session_id
    c.execute("""
        CREATE TABLE IF NOT EXISTS memory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT,
            role TEXT,
            message TEXT,
            timestamp TEXT
        )
    """)
    c.execute(
        "INSERT INTO memory (session_id, role, message, timestamp) VALUES (?, ?, ?, ?)",
        (data.session_id, data.role or "", data.message, datetime.now(timezone.utc).isoformat())
    )
    conn.commit()
    return {"status": "saved"}


@router.get("/all/")
def get_all_memory(session_id: Optional[str] = None) -> List[dict]:
    """Return recent memory entries. If session_id is provided, filter to that session."""
    conn = get_db()
    c = conn.cursor()
    if session_id:
        c.execute(
            "SELECT * FROM memory WHERE session_id = ? ORDER BY id DESC LIMIT 200",
            (session_id,)
        )
    else:
        c.execute("SELECT * FROM memory ORDER BY id DESC LIMIT 200")
    rows = c.fetchall()
    return [dict(row) for row in rows]


@router.get("/session/{session_id}/")
def get_memory_for_session(session_id: str) -> List[dict]:
    """Convenience endpoint to fetch memory for a specific session."""
    return get_all_memory(session_id=session_id)
