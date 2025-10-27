import hashlib, json
from modelsVS import Ballot

Included_fields = {"voterid", "upk", "ctv", "ctlv", "ctlid", "proof"}

def hash_ballot(ballot: Ballot) -> str:
    ballot_with_included_fields = ballot.model_dump(include=Included_fields) #python dict with included fields
    payload = json.dumps(ballot_with_included_fields)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()