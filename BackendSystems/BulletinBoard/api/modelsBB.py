from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional

class ElGamalParams(BaseModel):
    """Elliptic curve Elgamal cryptographic parameters.
    All parameters are encoded for safe transport in JSON-format."""
    group: int
    generator: str  # base64-encoded group generator
    order: str      # base64-encoded group order

class Candidate(BaseModel):
    """Candidate id and candidate name"""
    id: int
    name: str

class Voter(BaseModel):
    """Voter id and voter name"""
    id: int
    name: str

class Election(BaseModel):
    """Election metadata."""
    id: int
    name: str
    start: datetime #should be ISO format
    end: datetime

class Elections(BaseModel):
    """Container for multiple elections."""
    elections: List[Election]

class NewElectionData(BaseModel):
    """Container for election metadata along with list of and eligble voters"""
    election: Election
    candidates: List[Candidate] = []
    voters: List[Voter] = []

class VoterKey(BaseModel):
    """Container for a voter's public key for a specific election."""
    electionid: int
    voterid: int
    publickey: str # base64-encoded public key

class VoterKeyList(BaseModel):
    """Container for list of voter public keys for specific election."""
    voterkeylist: List[VoterKey]

# class KeyPair(BaseModel):
#     """Container for public keys for Tallying Server and Voting Server."""
#     publickeyTS: str # base64-encoded public key
#     publickeyVS: str # base64-encoded public key

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

class CandidateResult(BaseModel):
    """Result for a single candiate.
    Contains number of votes received and NIZK proof.
    """
    candidateid: int 
    votes: int
    proof: str          # base64-encoded NIZK proof of correct decryption created when tallying.

class ElectionResult(BaseModel):
    """Result for entire election.
    Results for each individual candidate are gathered in a list.
    """
    electionid: int
    result: list[CandidateResult]

class IndexImage(BaseModel):
    """Container for ballot image and timestamp associated with
    its position on the voter CBR."""
    cbrindex: int           # CBR index of ballot.
    image: str              # Image filepath for ballot at certain CBR index.
    timestamp: datetime     # Timestamp for ballot at certain CBR index.

class IndexImageCBR(BaseModel):
    """Container for CBR images and timestamps for a given voter."""
    cbrimages: List[IndexImage]     # List of CBR images and timestamps for a given voter.