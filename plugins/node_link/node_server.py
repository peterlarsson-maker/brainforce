import time
import yaml
from pathlib import Path
from fastapi import FastAPI, Body
from pydantic import BaseModel
import uvicorn

ROOT = Path(__file__).resolve().parents[2]  # repo root
CONFIG = ROOT / "config" / "grid_nodes.yml"
START = time.time()

class Thought(BaseModel):
    text: str

def load_cfg():
        if CONFIG.exists():
            with open(CONFIG, "r", encoding="utf-8") as f:
                return yaml.safe_load(f) or {}
        return {}

app = FastAPI(title="Brainforce Node Link")

@app.get("/ping")
def ping():
    cfg = load_cfg()
    node_id = (cfg.get("self") or {}).get("id", "node-unknown")
    return {"ok": True, "node": node_id}

@app.post("/thought")
def thought(t: Thought):
    # Placeholder: forward into core/memory or queue
    return {"received": True, "len": len(t.text)}

@app.get("/status")
def status():
    return {"uptime_sec": int(time.time() - START)}

@app.get("/nodes")
def nodes():
    cfg = load_cfg()
    return {"self": cfg.get("self", {}), "peers": cfg.get("peers", [])}

if __name__ == "__main__":
    cfg = load_cfg()
    host = "127.0.0.1"
    port = 8100
    if "self" in cfg and isinstance(cfg["self"], dict):
        h = cfg["self"].get("host", "")
        if isinstance(h, str) and "://" in h:
            try:
                hp = h.split("://",1)[1]
                parts = hp.split(":")
                if len(parts) == 2:
                    host = "0.0.0.0" if parts[0] in ("localhost","127.0.0.1") else parts[0]
                    port = int(parts[1])
            except Exception:
                pass
    uvicorn.run(app, host=host, port=port)