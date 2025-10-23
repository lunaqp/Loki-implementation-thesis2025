import queries as db
from fastapi import FastAPI, Query, HTTPException
from modelsBB import ElGamalParams, NewElectionData, VoterKeyList, Ballot, BallotWithElectionid
import base64
import dbcalls as db
from notifications import notify_ts_vs_params_saved, notify_ra_public_key_saved
import asyncio

app = FastAPI()

@app.get("/health")
def health():
    return{"ok": True}

@app.get("/hello") #Defines HTTP Get route at /hello
#a function that runs when client requests /hello
def hello():
    return {"message": "Hello World from BulletinBoard!"}

@app.get("/candidates")
def candidates(election_id: int = Query(..., description = "id of the election")):
    candidates = db.fetch_candidates_for_election(election_id)
    candidates_dict = [{"id": cid, "name": name} for cid, name in candidates]
    return {"candidates": candidates_dict}

@app.get("/voters")
def voters(election_id: int = Query(..., description = "id of the election")):
    voters = db.fetch_voters_for_election(election_id)
    voters_dict = [{"id": vid, "name": name} for vid, name in voters]
    return {"voters": voters_dict}

@app.get("/elgamalparams")
async def get_params():
    GROUP, GENERATOR, ORDER = await db.fetch_params()

    return {
    "group": GROUP,
    "generator": base64.b64encode(GENERATOR).decode(), # Base 64 encoded for tranfer
    "order": base64.b64encode(ORDER).decode(),  # Base 64 encoded for tranfer
    }

@app.post("/receive-params")
async def receive_params(params: ElGamalParams):
    GROUP = params.group
    GENERATOR = base64.b64decode(params.generator)
    ORDER = base64.b64decode(params.order)

    # Creating an async loop for the database access since psycopg2 only allows syncronized access.
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, db.save_elgamalparams, GROUP, GENERATOR, ORDER)
    await notify_ts_vs_params_saved()

    return {"status": "ElGamal parameters saved"}

@app.post("/receive-public-key")
async def receive_key(payload: dict):
    service = payload.get("service")
    KEY = base64.b64decode(payload.get("key"))
    db.save_key_to_db(service, KEY)
    await notify_ra_public_key_saved(service)

    return {"status": f"{service} public key saved"}

# receives election data from RA and loads it into the database.
@app.post("/receive-election")
async def receive_election(payload: NewElectionData):
    db.load_election_into_db(payload)
    print(f"election loaded with id {payload.election.id}")
    
    return {"status": "new election loaded into database"}

@app.post("/receive-ballot0")
async def receive_ballot0(pyBallot:Ballot):
    try:
        db.load_ballot_into_db(pyBallot)
        print(f"Ballot0 loaded with voter id {pyBallot.voterid}")
    
        return {"status": "new ballot0 loaded into database"}
    except Exception as e:
        print(f"[BB] load_ballot0_into_db failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    
@app.post("/receive-ballot")
async def receive_ballot(pyBallot:Ballot):
    try:
        db.load_ballot_into_db(pyBallot)
        print(f"Ballot loaded with voter id {pyBallot.voterid}")
    
        return {"status": "new ballot loaded into database"}
    except Exception as e:
        print(f"[BB] load_ballot_into_db failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# receives public keys for voters for a given election from RA and loads them into the database.
@app.post("/receive-voter-keys")
async def receive_voter_keys(payload: VoterKeyList):
    db.save_voter_keys_to_db(payload)

@app.post("/send-election-startdate")
async def send_election_startdate(payload: dict):
    election_startdate, election_enddate = db.fetch_election_dates(payload.get("electionid"))

    # Convert to ISO 8601 string for transfer
    formatted_startdate = election_startdate.isoformat()
    formatted_enddate = election_enddate.isoformat()

    return {"startdate": formatted_startdate, "enddate": formatted_enddate}

@app.get("/public-keys-tsvs")
async def send_public_keys_tsvs():
    public_key_ts_bin, public_key_vs_bin = db.fetch_public_keys_tsvs()
    public_key_ts_b64 = base64.b64encode(public_key_ts_bin)
    public_key_vs_b64 = base64.b64encode(public_key_vs_bin)
    
    return {"publickey_ts": public_key_ts_b64, "publickey_vs": public_key_vs_b64}

@app.get("/voter-public-key")
def voter_public_key(
    voter_id: int = Query(..., description="ID of the voter"),
    election_id: int = Query(..., description="ID of the election")
):
    voter_public_key_bin = db.fetch_voter_public_key(voter_id, election_id)
    voter_public_key_b64 = base64.b64encode(voter_public_key_bin).decode()

    return {"voter_public_key": voter_public_key_b64}
