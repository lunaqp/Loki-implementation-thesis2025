from pydantic import BaseModel
from typing import List
from typing import Optional
from datetime import datetime

class ElGamalParams(BaseModel):
    """Elliptic curve Elgamal cryptographic parameters.
    All parameters are encoded for safe transport in JSON-format."""
    group: int
    generator: str  # base64-encoded group generator
    order: str      # base64-encoded group order

class Ballot(BaseModel):
    """Encrypted ballot submitted by a voter.

    Contains voter id, encrypted ballot components,
    optional data added during processing, and proof material.
    """
    voterid: int
    upk: str                                # Voter public key (base64-encoded).
    ctv: List[List[str]]                    # List of encrypted candidate choice.
    ctlv: List[str]                         # Encrypted list of CBR indices for previous voter-cast ballots - as provided by voter.
    ctlid: List[str]                        # Encrypted list of CBR indices for previous voter-cast ballots - correct representation.
    proof: str                              # NIZK proof verifying the correct construction of the ballot.
    electionid: Optional[int] = None
    timestamp: Optional[datetime] = None
    hash: Optional[str] = None              # Hash-value for ballot to ensure uniqueness on BB CBR.
    imagepath: Optional[str] = None         # Filename for image associated with ballot.

class VoterCastBallot(BaseModel):
    """Container for unencrypted ballot cast from VA frontend."""
    v: int              # Selected candidate.
    lv_list: list       # voter provided list of previous ballot indices.
    election_id: int    

class AuthRequest(BaseModel):
    """Authentication request payload."""
    provided_username: str
    provided_password: str

class Election(BaseModel):
    """Election metadata."""
    id: int
    name: str
    start: datetime #should be ISO format
    end: datetime

class Elections(BaseModel):
    """Container for multiple elections."""
    elections: List[Election]

class IndexImage(BaseModel):
    """Container for ballot image and timestamp associated with
    its position on the voter CBR."""
    cbrindex: int           # CBR index of ballot.
    image: str              # Image filepath for ballot at certain CBR index.
    timestamp: datetime     # Timestamp for ballot at certain CBR index.
    
class IndexImageCBR(BaseModel):
    """Container for tuples of CBR indices, images, and timestamps for a given voter."""
    cbrimages: List[IndexImage]     # List of CBR indices, images, and timestamps for a given voter.

class CandidateResult(BaseModel):
    """Result for a single candiate.
    Contains number of votes received and NIZK proof.
    """
    candidateid: int 
    votes: int
    proof: str      # base64-encoded NIZK proof of correct decryption created when tallying.

class ElectionResult(BaseModel):
    """Result for entire election.
    Results for each individual candidate are gathered in a list.
    """
    electionid: int
    result: list[CandidateResult]