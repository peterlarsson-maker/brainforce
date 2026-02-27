from fastapi import APIRouter, HTTPException, Request, Header, Depends
from pydantic import BaseModel
import os

from typing import List, Dict
from core import memory as memory_module
from core.memory import MemorySave
from core.auth import get_current_user

router = APIRouter()

class OpenAIRequest(BaseModel):
    prompt: str
    model: str = "gpt-3.5-turbo"
    temperature: float = 0.7
    max_tokens: int = 512

@router.post("/openai/")
def openai_proxy(
    req: OpenAIRequest,
    session_id: str = Header(None, alias="X-Session-Id"),
    current_user: dict = Depends(get_current_user)
):
    """Proxy to OpenAI that requires an X-Session-Id header for tracking.

    The session_id is required for downstream memory and logging.
    """
    if not session_id:
        raise HTTPException(status_code=400, detail="X-Session-Id header is required")

    # Persist the incoming user prompt so history is durable and complete
    try:
        memory_module.save_memory(
            MemorySave(
                session_id=session_id,
                role="user",
                message=req.prompt,
                user_id=current_user["id"],
            ),
            current_user=current_user,
        )
    except Exception as exc:
        # log to stdout for debugging; we intentionally do not abort the request
        print(f"warning: failed to save prompt memory: {exc}")

    # Fetch recent memory for this session
    try:
        history = memory_module.get_all_memory(session_id=session_id, current_user=current_user) or []
    except Exception:
        history = []

    # memory.get_all_memory returns newest-first. Use a simple token-estimate heuristic
    # and prefer including full turns (user+assistant pairs).
    # Allow configuring the token budget via environment variable
    DEFAULT_TOKEN_BUDGET = 3000
    TOKEN_BUDGET = DEFAULT_TOKEN_BUDGET
    env_val = os.getenv("MEMORY_TOKEN_BUDGET")
    if env_val is not None:
        try:
            TOKEN_BUDGET = int(env_val)
        except Exception:
            TOKEN_BUDGET = DEFAULT_TOKEN_BUDGET

    def estimate_tokens(s: str) -> int:
        return max(1, (len(s) + 3) // 4)

    # Build turns from newest-first history. Each turn is a tuple (user_entry, assistant_entry)
    turns_newest_first: List[tuple] = []
    i = 0
    while i < len(history):
        entry = history[i]
        role = (entry.get("role") or "").lower()
        if role == "assistant":
            # try to pair with a user entry after this assistant
            if i + 1 < len(history) and (history[i + 1].get("role") or "").lower() == "user":
                user_entry = history[i + 1]
                assistant_entry = entry
                turns_newest_first.append((user_entry, assistant_entry))
                i += 2
            else:
                # assistant without paired user
                turns_newest_first.append((None, entry))
                i += 1
        elif role == "user":
            # user without assistant yet
            turns_newest_first.append((entry, None))
            i += 1
        else:
            # other roles treated as single-message user turns
            turns_newest_first.append((entry, None))
            i += 1

    included_turns_newest_first: List[tuple] = []
    total_tokens = 0
    seen_user_included = False
    for user_entry, assistant_entry in turns_newest_first:
        user_text = (user_entry.get("message") if user_entry else "") or ""
        assistant_text = (assistant_entry.get("message") if assistant_entry else "") or ""
        t_user = estimate_tokens(user_text)
        t_assist = estimate_tokens(assistant_text) if assistant_text else 0

        if not seen_user_included and user_text:
            # Always include the most recent user message even if it exceeds the budget.
            # Include assistant reply in the same turn only if it fits.
            included_turns_newest_first.append((user_entry, assistant_entry))
            total_tokens += t_user
            if assistant_text and total_tokens + t_assist <= TOKEN_BUDGET:
                total_tokens += t_assist
            seen_user_included = True
            continue

        # For subsequent turns include the full turn only if it fits in remaining budget
        if total_tokens + t_user + t_assist <= TOKEN_BUDGET:
            included_turns_newest_first.append((user_entry, assistant_entry))
            total_tokens += t_user + t_assist
        else:
            # stop when budget exhausted
            break

    # Flatten included turns to messages (oldest-first)
    recent_oldest_first: List[Dict] = []
    for user_entry, assistant_entry in reversed(included_turns_newest_first):
        if user_entry:
            recent_oldest_first.append({"role": user_entry.get("role", "user"), "content": user_entry.get("message", "")})
        if assistant_entry:
            recent_oldest_first.append({"role": assistant_entry.get("role", "assistant"), "content": assistant_entry.get("message", "")})

    messages: List[Dict] = recent_oldest_first

    if os.getenv("MOCK_MODE") == "1":
        # In mock mode, synthesize an assistant reply and persist it
        assistant_text = f"MOCK_REPLY: reply to {req.prompt[:64]}"
        # Persist assistant reply to memory (include user context)
        try:
            memory_module.save_memory(
                MemorySave(
                    session_id=session_id,
                    role="assistant",
                    message=assistant_text,
                    user_id=current_user["id"],
                ),
                current_user=current_user,
            )
        except Exception:
            pass
        return {"response": assistant_text, "session_id": session_id, "messages": messages}

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise HTTPException(status_code=403, detail="Ingen API-nyckel satt")

    # the session_id and user are implicitly associated; we don't allow an external
    # caller to pretend to be someone else by setting the header differently.
    # (current_user is already validated above.)

    # import requests lazily so module import works even when requests isn't installed
    import requests

    resp = requests.post(
        "https://api.openai.com/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        },
        json={
            "model": req.model,
            "messages": messages,
            "temperature": req.temperature,
            "max_tokens": req.max_tokens
        }
    )
    # Pass session id back so caller can correlate logs/memory
    result = resp.json()

    # Try to extract assistant reply text and persist it to memory
    assistant_text = None
    try:
        if isinstance(result, dict) and "choices" in result:
            assistant_text = result["choices"][0]["message"]["content"]
        elif isinstance(result, dict) and "response" in result:
            assistant_text = result.get("response")
    except Exception:
        assistant_text = None

    if assistant_text:
        try:
            memory_module.save_memory(
                MemorySave(
                    session_id=session_id,
                    role="assistant",
                    message=assistant_text,
                    user_id=current_user["id"],
                ),
                current_user=current_user,
            )
        except Exception as exc:
            print(f"warning: failed to save assistant memory: {exc}")

    if isinstance(result, dict):
        result.setdefault("session_id", session_id)
    return result
