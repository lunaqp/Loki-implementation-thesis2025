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

class AuthRequest(BaseModel):
    provided_username: str
    provided_password: str

class Election(BaseModel):
    id: int
    name: str
    start: datetime #should be ISO format
    end: datetime

class Elections(BaseModel):
    elections: List[Election]

class IndexImage(BaseModel):
    cbrindex: int
    image: str
    timestamp: datetime
    
class IndexImageCBR(BaseModel):
    cbrimages: List[IndexImage]

class CandidateResult(BaseModel):
    candidateid: int
    votes: int
    proof: str # base64-encoded

class ElectionResult(BaseModel):
    electionid: int
    result: list[CandidateResult]