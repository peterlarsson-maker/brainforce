import time, json
from pathlib import Path

LOG_DIR = Path(__file__).resolve().parents[3] / "status" / "grid"
LOG_DIR.mkdir(parents=True, exist_ok=True)
LOG = LOG_DIR / "consensus.log"

def append(record: dict) -> str:
    rec = {"ts": int(time.time()), **record}
    LOG.write_text((LOG.read_text(encoding="utf-8") if LOG.exists() else "") + json.dumps(rec, ensure_ascii=False) + "\n", encoding="utf-8")
    return LOG.as_posix()