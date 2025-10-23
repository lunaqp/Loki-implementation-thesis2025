from pydantic import BaseModel
from typing import List
from datetime import datetime

class Ballot(BaseModel):
    voterid: int
    upk: str
    ctv: List[List[str]]
    ctlv: List[str] 
    ctlid: List[str] 
    proof: str

class BallotPayload(BaseModel):
    electionid: int
    ballot0list: List[Ballot]

class ElGamalParams(BaseModel):
    group: int
    generator: str # base64-encoded
    order: str # base64-encoded

class BallotWithHash(BaseModel):
    hash: str
    ballot: Ballot

class BallotWithElectionid(BaseModel):
    ballot: Ballot
    electionid: int
    timestamp: datetime