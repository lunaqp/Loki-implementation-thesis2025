from fastapi import FastAPI, HTTPException
import asyncio
from keygen import send_public_key_to_BB
from modelsVS import BallotPayload, Ballot
from validateBallot import validate_ballot, obfuscate
from epochGeneration import save_timestamps_for_voter, fetch_ballot0_timestamp, fetch_ballot_timestamp_and_imagepath, duckdb_lock
from contextlib import asynccontextmanager
import duckdb
import httpx
from hashVS import hash_ballot
from epochHandling import update_time, send_ballot0_to_bb
import base64


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialising DuckDB database:
    conn = duckdb.connect("/duckdb/voter-data.duckdb")
    conn.sql("CREATE TABLE IF NOT EXISTS VoterTimestamps(VoterID INTEGER, ElectionID INTEGER, Timestamp TIMESTAMPTZ, Processed BOOLEAN, ImagePath TEXT)" )
    conn.sql("CREATE TABLE IF NOT EXISTS PendingVotes(VoterID INTEGER, ElectionID INTEGER, PublicKey BLOB, ctv TEXT, ctlv TEXT, ctlid TEXT, Proof BLOB)")

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
    conn = duckdb.connect("/duckdb/voter-data.duckdb") # for printing tables when testing
    conn.table("VoterTimestamps").show() # for printing tables when testing

    # NOTE: Validate ballots before sending to CBR via BB.

    return {"status": "ok"}

@app.post("/receive-ballot")
async def receive_ballot(pyBallot: Ballot):
    try:
        async with duckdb_lock: # lock is acquired to check if access should be allowed, lock while accessing ressource and is then released before returning  
            conn = duckdb.connect("/duckdb/voter-data.duckdb")
            public_key = base64.b64decode(pyBallot.upk)
            proof = base64.b64decode(pyBallot.proof)
            conn.execute("INSERT INTO PendingVotes (VoterID, ElectionID, PublicKey, ctv, ctlv, ctlid, Proof) VALUES (?, ?, ?, ?, ?, ?, ?)", (pyBallot.voterid, pyBallot.electionid, public_key, pyBallot.ctv, pyBallot.ctlv, pyBallot.ctlid, proof)) 
            conn.table("PendingVotes").show()
        conn.close()
    except Exception as e:
        print(f"error writing ballot to duckdb for voter {pyBallot.voterid} in election {pyBallot.electionid}: {e}")

