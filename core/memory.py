from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, timezone
from core.database import get_db
from core.auth import get_current_user

router = APIRouter()


class MemorySave(BaseModel):
    session_id: str
    role: Optional[str] = ""
    message: str
    # user_id is filled in by the server (not accepted from the client)
    user_id: Optional[int] = None


@router.post("/save/")
def save_memory(data: MemorySave, current_user: dict = Depends(get_current_user)):
    """Save a memory entry tied to a session_id and the authenticated user."""
    if not data.session_id:
        raise HTTPException(status_code=400, detail="session_id is required")

    uid = current_user["id"]
    conn = get_db()
    c = conn.cursor()
    # session_id must not be reused by another user
    c.execute("SELECT user_id FROM memory WHERE session_id = ? LIMIT 1", (data.session_id,))
    row = c.fetchone()
    if row and row["user_id"] != uid:
        raise HTTPException(status_code=400, detail="session_id already used by another user")

    # ensure schema is still present (init_db handles this on startup too)
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
    c.execute(
        "INSERT INTO memory (session_id, user_id, role, message, timestamp) VALUES (?, ?, ?, ?, ?)",
        (data.session_id, uid, data.role or "", data.message, datetime.now(timezone.utc).isoformat())
    )
    conn.commit()
    return {"status": "saved"}


@router.get("/all/")
def get_all_memory(session_id: Optional[str] = None, current_user: dict = Depends(get_current_user)) -> List[dict]:
    """Return recent memory entries for the authenticated user.

    If session_id is provided, filter to that session; otherwise return all for the user.
    """
    uid = current_user["id"]
    conn = get_db()
    c = conn.cursor()
    if session_id:
        c.execute(
            "SELECT * FROM memory WHERE session_id = ? AND user_id = ? ORDER BY id DESC LIMIT 200",
            (session_id, uid)
        )
    else:
        c.execute("SELECT * FROM memory WHERE user_id = ? ORDER BY id DESC LIMIT 200", (uid,))
    rows = c.fetchall()
    return [dict(row) for row in rows]


@router.get("/session/{session_id}/")
def get_memory_for_session(session_id: str, current_user: dict = Depends(get_current_user)) -> List[dict]:
    """Convenience endpoint to fetch memory for a specific session (user scoped)."""
    return get_all_memory(session_id=session_id, current_user=current_user)