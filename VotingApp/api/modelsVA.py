from pydantic import BaseModel
from typing import List
from typing import Optional
from datetime import datetime

class ElGamalParams(BaseModel):
    group: int
    generator: str # base64-encoded
    order: str # base64-encoded

class Ballot(BaseModel):
    voterid: int
    upk: str
    ctv: List[List[str]]
    ctlv: List[str] 
    ctlid: List[str] 
    proof: str
    electionid: Optional[int] = None
    timestamp: Optional[datetime] = None
    hash: Optional[str] = None
    imagepath: Optional[str] = None

class VoterBallot(BaseModel):
    v: int
    lv_list: list
    election_id: int
    voter_id: int
