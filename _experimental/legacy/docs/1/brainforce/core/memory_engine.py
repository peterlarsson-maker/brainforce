"""
Memory Engine for BrainForce Apollo
Handles saving, loading, and searching memories using SQLite + optional FAISS.
"""

import os
import sqlite3
import json
import numpy as np
from datetime import datetime
from typing import List, Dict, Optional
from core import embedding_engine

# --- Optional FAISS support ---
try:
    import faiss
    FAISS_AVAILABLE = True
except ImportError:
    print("[MemoryEngine] FAISS not installed. Using Python fallback.")
    FAISS_AVAILABLE = False

# --- Paths ---
BASE_DIR = os.path.dirname(__file__)
KNOWLEDGE_DIR = os.path.join(BASE_DIR, "../knowledge")
os.makedirs(KNOWLEDGE_DIR, exist_ok=True)

DB_PATH = os.path.join(KNOWLEDGE_DIR, "memory.db")
FAISS_PATH = os.path.join(KNOWLEDGE_DIR, "memory.index")

# --- SQLite setup ---
def init_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS memories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            source TEXT,
            text TEXT,
            embedding TEXT,
            tags TEXT
        )
        """
    )
    conn.commit()
    conn.close()
init_db()


# --- Helper: FAISS index handling ---
def build_faiss_index():
    if not FAISS_AVAILABLE:
        return None

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT id, embedding FROM memories WHERE embedding IS NOT NULL")
    rows = cur.fetchall()
    conn.close()

    if not rows:
        return None

    embeddings = []
    ids = []
    for r in rows:
        try:
            emb = np.array(json.loads(r[1]), dtype=np.float32)
            embeddings.append(emb)
            ids.append(r[0])
        except Exception:
            pass

    dim = len(embeddings[0]) if embeddings else 384
    index = faiss.IndexIDMap(faiss.IndexFlatL2(dim))
    if embeddings:
        index.add_with_ids(np.array(embeddings), np.array(ids))
        faiss.write_index(index, FAISS_PATH)
        print(f"[MemoryEngine] FAISS index built with {len(ids)} items.")
    return index


def load_faiss_index():
    if not (FAISS_AVAILABLE and os.path.exists(FAISS_PATH)):
        return None
    try:
        return faiss.read_index(FAISS_PATH)
    except Exception as e:
        print("[MemoryEngine] Could not load FAISS index:", e)
        return None


FAISS_INDEX = load_faiss_index() or build_faiss_index()


# --- Core Functions ---
def save_memory(text: str, source: str = "system", tags: Optional[List[str]] = None) -> int:
    """Embed and save a memory item."""
    if not text.strip():
        return -1

    embedding = embedding_engine.embed_text([text])[0]
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO memories (timestamp, source, text, embedding, tags) VALUES (?, ?, ?, ?, ?)",
        (
            datetime.utcnow().isoformat(),
            source,
            text,
            json.dumps(embedding),
            ",".join(tags) if tags else "",
        ),
    )
    conn.commit()
    row_id = cur.lastrowid
    conn.close()

    # Update FAISS index
    if FAISS_AVAILABLE and embedding is not None:
        global FAISS_INDEX
        if FAISS_INDEX is None:
            dim = len(embedding)
            FAISS_INDEX = faiss.IndexIDMap(faiss.IndexFlatL2(dim))
        vec = np.array([embedding], dtype=np.float32)
        FAISS_INDEX.add_with_ids(vec, np.array([row_id]))
        faiss.write_index(FAISS_INDEX, FAISS_PATH)

    return row_id


def get_memory(id: int) -> Optional[Dict]:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT * FROM memories WHERE id=?", (id,))
    row = cur.fetchone()
    conn.close()
    if not row:
        return None
    return {
        "id": row[0],
        "timestamp": row[1],
        "source": row[2],
        "text": row[3],
        "tags": row[5].split(",") if row[5] else [],
    }


def list_memories(limit: int = 20) -> List[Dict]:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT id, timestamp, source, text, tags FROM memories ORDER BY id DESC LIMIT ?", (limit,))
    rows = cur.fetchall()
    conn.close()
    return [
        {
            "id": r[0],
            "timestamp": r[1],
            "source": r[2],
            "text": r[3],
            "tags": r[4].split(",") if r[4] else [],
        }
        for r in rows
    ]


def search_memory(query: str, limit: int = 5) -> List[Dict]:
    """Semantic or cosine-similarity search depending on FAISS availability."""
    query_vec = embedding_engine.embed_text([query])[0]

    if FAISS_AVAILABLE and FAISS_INDEX is not None:
        qv = np.array([query_vec], dtype=np.float32)
        D, I = FAISS_INDEX.search(qv, limit)
        ids = [int(i) for i in I[0] if i != -1]
        results = []
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        for i in ids:
            cur.execute("SELECT id, text, source, tags FROM memories WHERE id=?", (i,))
            r = cur.fetchone()
            if r:
                results.append(
                    {"id": r[0], "text": r[1], "source": r[2], "tags": r[3].split(",") if r[3] else []}
                )
        conn.close()
        return results

    # Fallback: naive cosine similarity in Python
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT id, text, embedding, source, tags FROM memories")
    rows = cur.fetchall()
    conn.close()

    scored = []
    for r in rows:
        try:
            emb = np.array(json.loads(r[2]), dtype=np.float32)
            score = np.dot(query_vec, emb) / (np.linalg.norm(query_vec) * np.linalg.norm(emb))
            scored.append((score, r))
        except Exception:
            pass

    scored.sort(key=lambda x: x[0], reverse=True)
    top = scored[:limit]
    return [
        {
            "id": r[1][0],
            "text": r[1][1],
            "source": r[1][3],
            "tags": r[1][4].split(",") if r[1][4] else [],
            "score": float(s),
        }
        for s, r in top
    ]

? Förklaring:
    • Bygger SQLite + FAISS hybridminne.
    • save_memory() ? sparar text + embedding.
    • search_memory() ? använder FAISS om möjligt, annars ren Python-sökning.
    • Allt sker helt lokalt.
    • Klarar flera tusen poster.

? Nästa fil:
context_builder.py – den som hämtar relevant kontext inför varje fråga.
Vill du att jag skickar fil 3 nu?
Du sade:
Ja
Code GPT sade:
Perfekt ?
Nu kommer fil 3 av 4 – context_builder.py
Den fungerar som hjärnans “främre pannlob” — hämtar relevanta minnen, kombinerar dem till kontext, och kan användas av alla moduler (eller framtida AI-modeller) för att bygga förståelse inför ett beslut eller svar.

? 3 / 4 – context_builder.py
