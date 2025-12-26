"""Ballot0 generation.

Includes:
- Fetching TS/VS public keys from BB
- ElGamal encryption function
- Ballot0 construction for each voter
- Serialization to pydantic models for transport to Voting Server
"""

from keygen import GROUP, GENERATOR, ORDER 
from petlib.ec import EcPt
from modelsRA import Ballot
from modelsRA import BallotPayload
import httpx
import base64
from coloursRA import CYAN, RED

async def generate_ballot0(voter_id, public_key_voter, candidates): 
    """Builds and Generate ballot0 for a voter. This is the initialisation ballot.
    Fetches public key from the Bulletin Board. 
    Builds ctbar (ctbar = (ctv, ctlv, ctlid, proof)).
    Bulids ballot0 (Ballot0 = id, public key, ctbar)

    Args:
        voter_id: Voter identifier.
        public_key_voter: Voter public key (as received/stored by the system).
        candidates: Number of candidates in the election.

    Returns:
        Ballot0 tuple ``(voter_id, public_key_voter, ct0, ctl0, ctlid, r0)`` where:
        - ``ct0`` is a list of ciphertext pairs for each candidate.
        - ``ctl0`` is a ciphertext under the VS key.
        - ``ctlid`` equals ``ctl0`` for ballot-0.
        - ``r0`` is the encryption randomness used.
    """
    public_key_TS, public_key_VS = await fetch_public_keys_from_bb()
    r0 = ORDER.random()
    x = [0]*candidates
    ct0 = [enc(GENERATOR, public_key_TS, x[j], r0) for j in range(candidates)]
    ctl0 = enc(GENERATOR, public_key_VS, 0, r0)
    ctlid = ctl0 # ctlid is identical to ctlv for ballot 0 since it sets "ctl0 = ctlid = enc(pk_vs, 0, r)".
    ballot0 = (voter_id, public_key_voter, ct0, ctl0, ctlid, r0)

    return ballot0

async def fetch_public_keys_from_bb():
    """Fetch TS and VS public keys from the Bulletin Board.

    Returns:
        tuple[EcPt, EcPt]: (public_key_ts, public_key_vs).

    RuntimeError:
        If the request fails.
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get("http://bb_api:8000/public-keys-tsvs")
            response.raise_for_status()

            data: dict = response.json()
            public_key_ts_bin = base64.b64decode(data["publickey_ts"])
            public_key_vs_bin = base64.b64decode(data["publickey_vs"])
            public_key_TS = EcPt.from_binary(public_key_ts_bin, GROUP)
            public_key_VS = EcPt.from_binary(public_key_vs_bin, GROUP)

            return public_key_TS, public_key_VS
    except Exception as e:
        print(f"{RED}Error fetching public keys for TS and VS {e}")

       
def enc(g, pk, m, r):
    """Encrypt a message using EC ElGamal encryption.

    Args:
        g: Group generator.
        pk: Ppublic key.
        m: Integer message to encrypt.
        r: Randomness.

    Returns:
        tuple: Ciphertext pair(c0, c1).
    """
    c0 = r*g
    c1 = m*g + r*pk
    
    return (c0, c1)

def serialise(ballot_list):
    """Serialize ballot0 list into pydantic ``Ballot`` objects for transportation to Voting Server.

    Args:
        ballot_list: List of ballot tuples produced by ``generate_ballot0``.

    Returns:
        list[Ballot]: Base64-encoded pydantic objects ready for transport.
    """
    serialised_ballot_list = []
    for ballot in ballot_list:
        id = ballot[0]
        upk = ballot[1]
        ctv = [[base64.b64encode(x.export()).decode(), base64.b64encode(y.export()).decode()] for (x, y) in ballot[2]]
        ctlv = [base64.b64encode(ballot[3][0].export()).decode(), base64.b64encode(ballot[3][1].export()).decode()]
        ctlid = [base64.b64encode(ballot[4][0].export()).decode(), base64.b64encode(ballot[4][1].export()).decode()]
        proof = base64.b64encode(ballot[5].binary()).decode()
  
        pyBallot = Ballot(
            voterid = id,
            upk = upk,
            ctv = ctv,
            ctlv = ctlv,
            ctlid = ctlid,
            proof = proof
        )
        serialised_ballot_list.append(pyBallot) 

    return serialised_ballot_list
    
async def send_ballotlist_to_votingserver(election_id, ballot_list):
    """Send  he serialized ballot0 list to the Voting Server.

    Args:
        election_id: Election identifier.
        ballot_list: Ballot0 tuples to serialize and send.

    HTTPException:
        If VS returns a non-success status code.
    """
    serialised_list = serialise(ballot_list)
    payload = BallotPayload(
        electionid=election_id,
        ballot0list=serialised_list
    )
    print(f"{CYAN}Sending ballot0 list to vs...")
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post("http://vs_api:8000/ballot0list", json=payload.model_dump()) 
            response.raise_for_status()
    except Exception as e:
        print(f"{RED}Error sending ballot 0 list", {e})