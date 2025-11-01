from .commit_log import append

def validate(proposal_id: str, result: dict) -> dict:
    ok = True if result else False
    append({"role":"validator","proposal_id":proposal_id,"ok":ok})
    return {"proposal_id": proposal_id, "ok": ok}