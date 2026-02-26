from fastapi import APIRouter, Request
import os
import json
from datetime import datetime, timezone

router = APIRouter()

LOG_DIR = os.path.join(os.path.dirname(__file__), "../logs")
os.makedirs(LOG_DIR, exist_ok=True)

@router.post("/event/")
async def log_event(req: Request):
    data = await req.json()
    log_path = os.path.join(LOG_DIR, f"{datetime.now(timezone.utc).date()}.log.json")
    with open(log_path, "a") as f:
        f.write(json.dumps({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            **data
        }) + "\n")
    return {"status": "logged"}
