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

    # # Optional validators to automatically encode/decode bytes
    # @classmethod
    # def from_raw(cls, group: str, generator_bytes: bytes, order_bytes: bytes):
    #     return cls(
    #         group=group,
    #         generator=base64.b64encode(generator_bytes).decode(),
    #         order=base64.b64encode(order_bytes).decode(),
    #     )

    # def generator_bytes(self) -> bytes:
    #     return base64.b64decode(self.generator)

    # def order_bytes(self) -> bytes:
    #     return base64.b64decode(self.order)