import json, time, hashlib
from pathlib import Path
from .key_manager import load_keys

LOG_DIR = Path(__file__).resolve().parents[2] / "status" / "audit"
LOG_DIR.mkdir(parents=True, exist_ok=True)
LOG = LOG_DIR / "audit.log"

def _sign(private_key, payload: bytes) -> str:
    sig = private_key.sign(payload)
    return sig.hex()

def append_event(event: dict) -> Path:
    event = {"ts": int(time.time()), **event}
    payload = json.dumps(event, sort_keys=True, separators=(",", ":")).encode("utf-8")
    priv, pub = load_keys()
    sig = _sign(priv, payload)
    rec = {
        "hash": hashlib.sha256(payload).hexdigest(),
        "sig": sig,
        "event": event,
    }
    LOG.write_text((LOG.read_text(encoding="utf-8") if LOG.exists() else "") + json.dumps(rec, ensure_ascii=False) + "\n", encoding="utf-8")
    return LOG

if __name__ == "__main__":
    p = append_event({"type":"test","actor":"system","msg":"hello"})
    print(f"wrote {p}")