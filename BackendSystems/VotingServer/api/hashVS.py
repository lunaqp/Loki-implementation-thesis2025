import hashlib, json
from modelsVS import Ballot

Included_fields = {"voterid", "upk", "ctv", "ctlv", "ctlid", "proof"}

def hash_ballot(ballot: Ballot) -> str:
    """Compute the hash of a ballot.
    The ballot is converted to a dictionary containing only the fields listed
    in `Included_fields`. This is to be able to reuse the pydantic "Ballot" with only some of the fields.
    The dictionary is then serialized to a JSON string and hashed using SHA-256.
    Args:
        ballot (Ballot): A Ballot model instance to hash.
    Returns:
        str: The SHA-256 hash of the ballot.
    """
    ballot_with_included_fields = ballot.model_dump(include=Included_fields) # python dict with included fields
    payload = json.dumps(ballot_with_included_fields)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()