"""
FastAPI service for the Voting Server (VS).

This module initializes the VS subsystem, manages lifecycle setup,
handles incoming ballots, communicates with the Bulletin Board (BB),
and persists voting-related data in two DuckDB tables.
"""
from fastapi import FastAPI
import asyncio
from keygen import send_public_key_to_BB
from modelsVS import BallotPayload, Ballot
from contextlib import asynccontextmanager
import duckdb
from epochHandling import update_time, prepare_election
import json
from coloursVS import RED, CYAN
from lock import duckdb_lock
from fetchFunctions import fetch_image_filename, fetch_electiondates_from_bb
import pytz
from datetime import datetime

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manages application startup and shutdown events.

    On startup, this function initializes the DuckDB database schema
    and starts a background task for keeping track of current time. Control is
    yielded back to FastAPI once initialization is complete.

    Args:
        app (FastAPI): The FastAPI application instance.
    """
    conn = duckdb.connect("/duckdb/voter-data.duckdb")
    conn.sql("DROP TABLE IF EXISTS VoterTimestamps")
    conn.sql("DROP TABLE IF EXISTS PendingVotes")
    conn.sql("CREATE TABLE VoterTimestamps(VoterID INTEGER, ElectionID INTEGER, Timestamp TIMESTAMPTZ, Processed BOOLEAN, ImagePath TEXT)" )
    conn.sql("CREATE TABLE PendingVotes(VoterID INTEGER, ElectionID INTEGER, PublicKey TEXT, ctv TEXT, ctlv TEXT, ctlid TEXT, Proof TEXT)")

    asyncio.create_task(update_time())
    yield

app = FastAPI(lifespan=lifespan)

@app.get("/health")
def health():
    """Return status response indicating the service is running."""
    return {"ok": True}

@app.get("/vs_resp")
async def vs_resp():
    """Handle Bulletin Board (BB) notification for parameter availability.

    This endpoint is triggered by the BB once cryptographic parameters
    (group, generator, and order) have been stored in the BB postgres database.
    It initiates key generation and sends the public key material back to the BB.

    Returns:
        dict: A status message describing the performed action.
    """
    asyncio.create_task(send_public_key_to_BB()) # Calling send_public_key_to_BB implicitly fetches group, g, and order from BB, generates keys, and sends them to BB.
    return {"service": "VS", "result": "VS fetched g and order from BB + created keymaterial and sent to BB"}

@app.post("/ballot0list")
async def receive_ballotlist(payload: BallotPayload):
    """Receive the initial list of ballots for an election.

    This endpoint is called when a new election is loaded. It triggers
    background processing to initialise handling of an election.

    Args:
        payload (BallotPayload): The payload containing election ID and
            the list of initial ballots.

    Returns:
        dict: Acknowledgement of successful receipt.
    """
    print(f"{CYAN}Received election {payload.electionid}, {len(payload.ballot0list)} ballots")
    asyncio.create_task(prepare_election(payload))

    return {"status": "ok"}

@app.post("/receive-ballot")
async def receive_ballot(pyBallot: Ballot):
    """Receive and store a single encrypted ballot.

    This endpoint validates whether the election is currently active,
    stores the ballot in the PendingVotes table, and returns the
    associated ballot image filename.

    Args:
        pyBallot (Ballot): The ballot submitted by the voter in the VotingApp.

    Returns:
        dict: A response containing either the ballot image filename
        or a rejection message if the election is inactive.
    """
    election_start, election_end = await fetch_electiondates_from_bb(pyBallot.electionid)
    tz = pytz.timezone('Europe/Copenhagen')
    current_time = datetime.now(tz)

    # Reject ballot if the election is not active. TODO: improve user experience in frontend.
    if current_time < election_start or current_time > election_end:
        print(f"{RED}Election not active, rejecting ballot")
        return {"image": "Ballot rejected"}
    try:
        async with duckdb_lock: # lock is acquired to check if access should be allowed, lock while accessing ressource and is then released before returning  
            conn = duckdb.connect("/duckdb/voter-data.duckdb")
            ctv = json.dumps(pyBallot.ctv) # json string of base64 encoding
            ctlv = json.dumps(pyBallot.ctlv)
            ctlid = json.dumps(pyBallot.ctlid)
            conn.execute("INSERT INTO PendingVotes (VoterID, ElectionID, PublicKey, ctv, ctlv, ctlid, Proof) VALUES (?, ?, ?, ?, ?, ?, ?)",
                         (pyBallot.voterid, pyBallot.electionid, pyBallot.upk, ctv, ctlv, ctlid, pyBallot.proof)) 
            conn.close()
        image_filename = await fetch_image_filename(pyBallot.electionid, pyBallot.voterid)
        return {"image": image_filename}
    except Exception as e:
        print(f"{RED}error writing ballot to duckdb for voter {pyBallot.voterid} in election {pyBallot.electionid}: {e}")

