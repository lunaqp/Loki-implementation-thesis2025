from pydantic import BaseModel

class ElGamalParams(BaseModel):
    group: int
    generator: str # base64-encoded
    order: str # base64-encoded

class CandidateResult(BaseModel):
    candidateid: int
    votes: int
    proof: str # base64-encoded

class ElectionResult(BaseModel):
    electionid: int
    result: list[CandidateResult]