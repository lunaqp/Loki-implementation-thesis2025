from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

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

class BallotWithHash(BaseModel):
    hash: str
    ballot: Ballot

class BallotPayload(BaseModel):
    electionid: int
    ballot0list: List[Ballot]

class ElGamalParams(BaseModel):
    group: int
    generator: str # base64-encoded
    order: str # base64-encoded

class VoterKey(BaseModel):
    electionid: int
    voterid: int
    publickey: str # base64 encoded

class VoterKeyList(BaseModel):
    voterkeylist: List[VoterKey]

class Candidate(BaseModel):
    id: int
    name: str

class Voter(BaseModel):
    id: int
    name: str

class Election(BaseModel):
    id: int
    name: str
    start: datetime 
    end: datetime

class NewElectionData(BaseModel):
    election: Election
    candidates: List[Candidate] = []
    voters: List[Voter] = []