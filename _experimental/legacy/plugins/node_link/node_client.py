import yaml, httpx
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CONFIG = ROOT / "config" / "grid_nodes.yml"

def load_cfg():
    if CONFIG.exists():
        with open(CONFIG, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    return {}

def ping(url: str):
    r = httpx.get(f"{url.rstrip('/')}/ping", timeout=5.0)
    r.raise_for_status()
    return r.json()

def ping_peers():
    cfg = load_cfg()
    peers = (cfg.get("peers") or [])
    out = []
    for p in peers:
        url = p.get("host") or ""
        if not url:
            continue
        try:
            out.append({"peer": url, "resp": ping(url)})
        except Exception as e:
            out.append({"peer": url, "error": str(e)})
    return out

if __name__ == "__main__":
    print(ping_peers())