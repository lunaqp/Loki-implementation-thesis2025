from keygen import GROUP, GENERATOR, ORDER 
from petlib.ec import EcPt
from modelsRA import Ballot
from modelsRA import BallotPayload
import httpx
import base64
from coloursRA import BLUE, RED

async def generate_ballot0(voter_id, public_key_voter, candidates): 
    # Build ctbar (ctbar = (ctv, ctlv, ctlid, proof))
    public_key_TS, public_key_VS = await fetch_public_keys_from_bb()
    r0 = ORDER.random()
    x = [0]*candidates
    ct0 = [enc(GENERATOR, public_key_TS, x[j], r0) for j in range(candidates)]
    ctl0 = enc(GENERATOR, public_key_VS, 0, r0)
    ctlid = ctl0 # ctlid is identical to ctlv for ballot 0 since it sets "ctl0 = ctlid = enc(pk_vs, 0, r)".
    # Build ballot (Ballot = (id, upk, ct_bar))
    ballot0 = (voter_id, public_key_voter, ct0, ctl0, ctlid, r0)

    return ballot0

async def fetch_public_keys_from_bb():
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get("http://bb_api:8000/public-keys-tsvs")
            response.raise_for_status() # gets http status code

            data: dict = response.json()
            public_key_ts_bin = base64.b64decode(data["publickey_ts"])
            public_key_vs_bin = base64.b64decode(data["publickey_vs"])
            public_key_TS = EcPt.from_binary(public_key_ts_bin, GROUP)
            public_key_VS = EcPt.from_binary(public_key_vs_bin, GROUP)

            return public_key_TS, public_key_VS
    except Exception as e:
        print(f"{RED}Error fetching public keys for TS and VS {e}")

       
# Encryption function
# Parameters: generator, public key to encrypt with, message to encrypt and randomness for encryption.
def enc(g, pk, m, r):
    c0 = r*g
    c1 = m*g + r*pk
    
    return (c0, c1)

# Serialising ballot 0 list into pydantic objects for transferring to VS
def serialise(ballot_list):
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
    serialised_list = serialise(ballot_list)
    payload = BallotPayload(
        electionid=election_id,
        ballot0list=serialised_list
    )
    print(f"{BLUE}Sending ballot0 list to vs...")
    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(30.0)) as client:
            response = await client.post("http://vs_api:8000/ballot0list", json=payload.model_dump()) 
            response.raise_for_status()
    except Exception as e:
        print(f"{RED}Error sending ballot 0 list", {e})