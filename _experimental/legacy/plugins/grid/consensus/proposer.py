import uuid
from .commit_log import append

def propose(payload: dict) -> dict:
    pid = str(uuid.uuid4())
    rec = {"role":"proposer","id":pid,"payload":payload}
    append(rec)
    return {"proposal_id": pid, "status":"proposed"}