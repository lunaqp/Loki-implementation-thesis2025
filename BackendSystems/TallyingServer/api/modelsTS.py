from pydantic import BaseModel

class ElGamalParams(BaseModel):
    """Elliptic curve Elgamal cryptographic parameters.
    All parameters are encoded for safe transport in JSON-format."""
    group: int
    generator: str  # base64-encoded group generator
    order: str      # base64-encoded group order

class CandidateResult(BaseModel):
    """Result for a single candiate.
    Contains number of votes received and NIZK proof.
    """
    candidateid: int 
    votes: int
    proof: str          # base64-encoded NIZK proof of correct decryption created when tallying.

class ElectionResult(BaseModel):
    """Result for entire election.
    Results for each individual candidate are gathered in a list.
    """
    electionid: int
    result: list[CandidateResult]