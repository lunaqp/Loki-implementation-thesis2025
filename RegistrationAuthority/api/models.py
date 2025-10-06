from pydantic import BaseModel
from typing import List

class Ballot(BaseModel):
    id: int
    upk: str
    ctv: List[List[str]]
    ctlv: List[str] 
    ctlid: List[str] 
    proof: str

class BallotPayload(BaseModel):
    electionid: int
    ballot0list: List[Ballot]