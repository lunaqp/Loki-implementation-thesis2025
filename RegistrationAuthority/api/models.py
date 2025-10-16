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