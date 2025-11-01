from .commit_log import append

def aggregate(proposal_id: str, parts: list[dict]) -> dict:
    out = {"proposal_id": proposal_id, "parts": parts}
    append({"role":"aggregator", **out})
    return out