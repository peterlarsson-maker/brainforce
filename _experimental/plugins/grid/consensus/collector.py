from .commit_log import append

def collect(proposal_id: str, votes: list[bool]) -> dict:
    yes = sum(1 for v in votes if v)
    no  = sum(1 for v in votes if not v)
    rec = {"role":"collector","proposal_id":proposal_id,"yes":yes,"no":no}
    append(rec)
    return {"proposal_id": proposal_id, "yes": yes, "no": no}