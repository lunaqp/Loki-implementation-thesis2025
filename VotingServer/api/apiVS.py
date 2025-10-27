from fastapi import FastAPI, HTTPException
import asyncio
from keygen import send_public_key_to_BB
from modelsVS import BallotPayload, Ballot, BallotWithElectionid
from validateBallot import validate_ballot, fetch_voter_public_key_from_bb
from epochGeneration import save_timestamps_for_voter, generate_timestamps, fetch_ballot0_timestamp
from contextlib import asynccontextmanager
import duckdb
import httpx
from hashVS import hash_ballot

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialising DuckDB database:
    conn = duckdb.connect("/duckdb/voter-timestamps.duckdb")
    conn.sql("CREATE TABLE IF NOT EXISTS VoterTimestamps(VoterID INTEGER, ElectionID INTEGER, Timestamp TIMESTAMPTZ, Processed BOOLEAN, ImagePath TEXT)")
    yield  # yielding control back to FastAPI

app = FastAPI(lifespan=lifespan)

@app.get("/health")
def health():
    return {"ok": True}

# Triggered by BB when BB has saved group, generator, and order to the database.
@app.get("/vs_resp")
async def vs_resp():
    asyncio.create_task(send_public_key_to_BB()) # Calling send_public_key_to_BB implicitly fetches group, g, and order from BB, generates keys, and sends them to BB.
    return {"service": "VS", "result": "VS fetched g and order from BB + created keymaterial and saved to BB"}

@app.post("/ballot0list")
async def receive_ballotlist(payload: BallotPayload):
    print(f"Received election {payload.electionid}, {len(payload.ballot0list)} ballots")

    for ballot in payload.ballot0list:
        await save_timestamps_for_voter(payload.electionid, ballot.voterid)
       
        ballot0_timestamp, image_path = await fetch_ballot0_timestamp(payload.electionid, ballot.voterid)

        pyBallot = Ballot(
            voterid = ballot.voterid,
            upk = ballot.upk,
            ctv = ballot.ctv,
            ctlv = ballot.ctlv, 
            ctlid = ballot.ctlid, 
            proof = ballot.proof,
            electionid = payload.electionid,
            timestamp = ballot0_timestamp,
            imagepath = image_path
        )
        # pyBallot.hash = hash_ballot(pyBallot) #test, is it the same hash produced
        # print("VS hash:", pyBallot.hash)
        await send_ballot0_to_bb(pyBallot)
    conn = duckdb.connect("/duckdb/voter-timestamps.duckdb") # for printing tables when testing
    conn.table("VoterTimestamps").show() # for printing tables when testing

    # NOTE: Validate ballots before sending to CBR via BB.

    return {"status": "ok"}

@app.post("/receive-ballot")
async def receive_ballot(pyBallot: Ballot):
    ballot_validated = validate_ballot(pyBallot)
    if ballot_validated: 
        send_ballot_to_bb(pyBallot)
        return ballot_validated
    else:
        return ballot_validated 


async def send_ballot_to_bb(pyBallot:Ballot):
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post("http://bb_api:8000/receive-ballot", content = pyBallot.model_dump_json())
            response.raise_for_status() # gets http status code
            print(f"ballot sent to BB for voter {pyBallot.voterid}")
            return response.json()
    except Exception as e:
        print(f"Error sending ballot: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to send ballot to BB: {str(e)}") 


async def send_ballot0_to_bb(pyBallot: Ballot):
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post("http://bb_api:8000/receive-ballot0", content = pyBallot.model_dump_json())
            response.raise_for_status() # gets http status code
            print(f"ballot0 sent to BB for voter {pyBallot.voterid}")
            return response.json()
    except Exception as e:
        print(f"Error sending ballot0: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to send ballot0 to BB: {str(e)}")  
