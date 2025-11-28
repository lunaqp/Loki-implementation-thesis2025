from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional

class ElGamalParams(BaseModel):
    group: int
    generator: str # base64-encoded
    order: str # base64-encoded

#pydandic models: when data is parsed to this model, it make automatic input validation and raises errors if fiels are missing or wrong
#pydandic: converts string "123" into int.parsing dates.
#Declares shape and type of the data object. ex. candidates: id, name
class Candidate(BaseModel):
    id: int
    name: str

class Voter(BaseModel):
    id: int
    name: str

class Election(BaseModel):
    id: int
    name: str
    start: datetime #should be ISO format
    end: datetime

class Elections(BaseModel):
    elections: List[Election]

#Defines whole request loader expects
class NewElectionData(BaseModel):
    election: Election
    candidates: List[Candidate] = []
    voters: List[Voter] = []

class VoterKey(BaseModel):
    electionid: int
    voterid: int
    publickey: str # base64 encoded

class VoterKeyList(BaseModel):
    voterkeylist: List[VoterKey]

class KeyPair(BaseModel):
    publickeyTS: str # base64 encoded
    publickeyVS: str # base64 encoded

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

class CandidateResult(BaseModel):
    candidateid: int
    votes: int
    proof: str # base64-encoded

class ElectionResult(BaseModel):
    electionid: int
    result: list[CandidateResult]

class IndexImage(BaseModel):
    cbrindex: int
    image: str
    timestamp: datetime

class IndexImageCBR(BaseModel):
    cbrimages: List[IndexImage]