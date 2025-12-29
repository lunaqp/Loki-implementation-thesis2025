from pydantic import BaseModel
from typing import List
from datetime import datetime
from typing import Optional

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

class BallotPayload(BaseModel):
    """Payload containing the initial list of ballot 0s for an election."""
    electionid: int
    ballot0list: List[Ballot]

class ElGamalParams(BaseModel):
    """Elliptic curve Elgamal cryptographic parameters.
    All parameters are encoded for safe transport in JSON-format."""
    group: int
    generator: str  # base64-encoded group generator
    order: str      # base64-encoded group order