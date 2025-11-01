from .proposer import propose
from .collector import collect
from .aggregator import aggregate
from .validator import validate

p = propose({"task":"demo","value":42})
c = collect(p["proposal_id"], [True, True, False])
a = aggregate(p["proposal_id"], [{"node":"n1","ok":True},{"node":"n2","ok":True},{"node":"n3","ok":False}])
v = validate(p["proposal_id"], a)
print("OK", p, c, a, v)