from fastapi import FastAPI
import asyncio
from keygen import send_public_key_to_BB
from modelsVS import BallotPayload, Ballot
from epochHandling import create_timestamps, timestamp_management, fetch_ballot0_timestamp, send_ballot0_to_bb, fetch_electiondates_from_bb
from contextlib import asynccontextmanager
import duckdb
from epochHandling import update_time
import json
from coloursVS import RED, CYAN
from lock import duckdb_lock

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialising DuckDB database:
    conn = duckdb.connect("/duckdb/voter-data.duckdb")
    conn.sql("CREATE TABLE IF NOT EXISTS VoterTimestamps(VoterID INTEGER, ElectionID INTEGER, Timestamp TIMESTAMPTZ, Processed BOOLEAN, ImagePath TEXT)" )
    conn.sql("CREATE TABLE IF NOT EXISTS PendingVotes(VoterID INTEGER, ElectionID INTEGER, PublicKey TEXT, ctv TEXT, ctlv TEXT, ctlid TEXT, Proof TEXT)")

    asyncio.create_task(update_time())
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
    print(f"{CYAN}Received election {payload.electionid}, {len(payload.ballot0list)} ballots")
    await asyncio.create_task(create_timestamps(payload.ballot0list, payload.electionid))

    for ballot in payload.ballot0list:
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

        await send_ballot0_to_bb(pyBallot)
    
    # After sending ballot 0 we create an asynchronous task for handling vote-casting to each voters CBR.
    start, end = await fetch_electiondates_from_bb(payload.electionid)
    for ballot in payload.ballot0list:
        asyncio.create_task(timestamp_management(ballot.voterid, payload.electionid, start, end))

    return {"status": "ok"}

@app.post("/receive-ballot")
async def receive_ballot(pyBallot: Ballot):
    try:
        async with duckdb_lock: # lock is acquired to check if access should be allowed, lock while accessing ressource and is then released before returning  
            conn = duckdb.connect("/duckdb/voter-data.duckdb")
            ctv = json.dumps(pyBallot.ctv) # json string of base64 encoding
            ctlv = json.dumps(pyBallot.ctlv)
            ctlid = json.dumps(pyBallot.ctlid)
            conn.execute("INSERT INTO PendingVotes (VoterID, ElectionID, PublicKey, ctv, ctlv, ctlid, Proof) VALUES (?, ?, ?, ?, ?, ?, ?)",
                         (pyBallot.voterid, pyBallot.electionid, pyBallot.upk, ctv, ctlv, ctlid, pyBallot.proof)) 
            conn.close()
    except Exception as e:
        print(f"{RED}error writing ballot to duckdb for voter {pyBallot.voterid} in election {pyBallot.electionid}: {e}")

