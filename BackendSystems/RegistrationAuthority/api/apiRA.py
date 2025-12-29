"""FastAPI service for the Regitration Authority.

This module includes:
- Sending ElGamal parameters to the Bulletin Board for a new election.
- Loading new election JSON files.
- Generating voter keys and persist them for retrieval (DuckDB)
- Ballot-0 generation and delivery to the voting server (VS)

Notes
-----
- Cryptographic operations are implemented using ``petlib`` elliptic-curve primitives.
- Voter secret/public keys are stored in DuckDB as raw bytes (BLOB).
- Public keys and other binary artifacts are base64-encoded when transported over HTTP.
"""


import os
from fastapi import FastAPI, HTTPException, Query
import json
from keygen import keygen, send_params_to_bb, send_keys_to_bb, fetch_keys_from_duckdb
from generateB0 import generate_ballot0, send_ballotlist_to_votingserver
from contextlib import asynccontextmanager
import httpx
from modelsRA import VoterKeyList, NewElectionData
from coloursRA import BLUE, RED, CYAN
import duckdb
import base64

DATA_DIR = os.getenv("DATA_DIR", "/app/data")
"""Directory that contains election JSON files"""

# Defining startup functionality before the application starts:
@asynccontextmanager
async def lifespan(app: FastAPI):
    """FastAPI lifespan.
    Runs at application startup:
    - Sends ElGamal parameters to the Bulletin Board.
    - Ensure the DuckDB schema exists for storing voter keys.
    - Yields control back to FastAPI once initialization is complete.

    Args:
        app: The FastAPI application instance.
    """

    await send_params_to_bb()

    conn = duckdb.connect("/duckdb/voter-keys.duckdb")
    conn.sql("CREATE TABLE IF NOT EXISTS VoterKeys(VoterID INTEGER, ElectionID INTEGER, SecretKey BLOB, PublicKey BLOB)")

    yield

app = FastAPI(lifespan=lifespan)

received_keys = {"VS": False, "TS": False}
"""Tracks whether VS and TS have published key material (via BB notification)"""

@app.get("/health")
def health():
    """Healthcheck endpoint.
    Returns status of service running.
    """
    return {"ok": True}

@app.post("/elections/load-file")
async def load_election_from_file(name: str = Query(..., description="Filename inside DATA_DIR")):
    """Load a new election from JSON file.

    This endpoint:
    - Checks if key materil from TS/VS is ready.
    - Loads election JSON from ``DATA_DIR``.
    - Sends election to BB.
    - Generates a per-voter key pair, stores keys in DuckDB, and publishes the voters public keys to Bulletin Board.
    - Generates ballot0 for each voter and sends ballot0-list to VS.
    - Notifies the Tallying Server that an election is ready.

    Args:
        name: Election JSON filename located inside ``DATA_DIR``.

    Returns:
        Status payload of election loaded with election id and filename.

    HTTPException:
        - 404 if the requested file does not exist.
        - 400 if JSON parsing/validation fails or TS notification fails.
    """
    if not all(received_keys.values()):
        print(f"{BLUE}Missing TS and VS key, not ready for elections yet.")
        return {"status": "Missing TS and VS key, not ready for elections yet."}
    else:
        path = os.path.join(DATA_DIR, name) #builds path in DATA_DIR
        if not os.path.isfile(path):
            raise HTTPException(status_code=404, detail=f"File not found: {path}")
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f) #reads and parses json file

            payload = NewElectionData.model_validate(data) #pyladic validation, converts raw dict into typed NewElectionData

            await send_election_to_bb(payload)

            voter_id_list = [voter.id for voter in payload.voters ]
            voter_key_list: VoterKeyList = await keygen(voter_id_list, payload.election.id)
            await send_keys_to_bb(voter_key_list)

            print(f"{CYAN}Keys ready! Generating ballot0 for each voter.")
            voter_id_upk_list = [(voter_key.voterid, voter_key.publickey) for voter_key in voter_key_list.voterkeylist]
            ballot0_list = []
            for voter_id, public_key_voter in voter_id_upk_list:
                ballot0 = await generate_ballot0(
                    voter_id,
                    public_key_voter,
                    len(payload.candidates),
                )
                ballot0_list.append(ballot0)
            await send_ballotlist_to_votingserver(payload.election.id, ballot0_list)

            # Notify tallying server of election:
            async with httpx.AsyncClient() as client:
                try:
                    response = await client.post("http://ts_api:8000/receive-election", json={"electionid": payload.election.id})
                    response.raise_for_status()
                    print(f"{CYAN}Tallying server notified of election with ID: {payload.election.id}")
                except Exception as e:
                    print(f"Error notifying tallying server: {e}")
                    raise HTTPException(status_code=400, detail=f"Tallying server error: {e}")

            return {"status": "loaded", "election_id": payload.election.id, "file": name}
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))

@app.post("/key_ready")
async def key_ready(payload: dict):
    """Receive notification from Bulletin Board when TS/VS key material is ready.

    Args:
        payload: JSON payload containing ``{"service": "VS"}`` or ``{"service": "TS"}``.

    Returns Acknowledgement response.
    """
    service = payload.get("service")
    print(f"{BLUE}Key material ready from {service}")
    received_keys[service] = True

    if all(received_keys.values()):
        print(f"{BLUE}Public keys generated by VS and TS. Ready for new elections")

    return {"ack": True}

async def send_election_to_bb(payload):
    """Send election data payload to the Bulletin Board.

    Args:
        Payload: Validated election data.

    Returns: 
        Parsed JSON response from BB.

    HTTPException:
        If the BB request fails.
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post("http://bb_api:8000/receive-election", content=payload.model_dump_json())
            response.raise_for_status() 
            print(f"{BLUE}election sent to BB with id {payload.election.id}")
            return response.json()
    except Exception as e:
        print(f"{RED}Error sending election payload: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to send election to BB: {str(e)}")        

@app.get("/voter-keys")
async def send_voter_keys(
    voter_id: int = Query(..., description="id of the voter"),
    election_id: int = Query(..., description="id of the election")):
    """Send a voter's key material for a given election, when requested by the voter.
    Keys are retrieved from DuckDB and encoded for transport.

    Args:
        voter_id: Voter identifier.
        election_id: Election identifier.

    Returns:
        dict[str, str]: ``{"secret_key": "...", "public_key": "..."}`` (base64-encoded).

    """
    print(f"sending keys to Voting-app for voter: {voter_id}")
    secret_key, public_key = fetch_keys_from_duckdb(voter_id, election_id)
    data: dict = {"secret_key": base64.b64encode(secret_key).decode(), "public_key": base64.b64encode(public_key).decode()} # decode() converts b64 bytes to string
    return data