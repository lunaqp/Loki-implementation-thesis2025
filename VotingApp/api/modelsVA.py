from pydantic import BaseModel
from typing import List

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