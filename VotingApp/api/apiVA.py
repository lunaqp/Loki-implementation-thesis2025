from fastapi import FastAPI, HTTPException
import os
from bulletin_routes import router as bulletin_router
import base64
import duckdb
from contextlib import asynccontextmanager
import httpx
from modelsVA import Ballot, VoterBallot
from vote_casting import vote

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialising DuckDB database:
    conn = duckdb.connect("/duckdb/voter-keys.duckdb")
    conn.sql("CREATE TABLE VoterKeys(VoterID INTEGER, ElectionID INTEGER, SecretKey BLOB, PublicKey BLOB)")
    yield  # yielding control back to FastAPI

app = FastAPI(lifespan=lifespan)

@app.get("/health")
def health():
    return{"ok": True}

# Register FastAPI router
app.include_router(bulletin_router)

@app.get("/api/election")
def get_election_id():
    return {"electionId": 123}

@app.post("/receive-keys")
def receive_secret_key(data: dict):
    voter_id = data["voter_id"]
    election_id = data["election_id"]
    enc_secret_key = data["secret_key"]
    public_key = data["public_key"]

    print(f"voterid: {voter_id}, electionid: {election_id}, secretkey: {enc_secret_key}, publickey: {public_key}")

    # Public and private keys are saved in internal duckdb database. Secret key is symmetrically encrypted with Fernet.
    save_keys_to_duckdb(voter_id, election_id, enc_secret_key, public_key)

    return {"status": "secret key received"}

def save_keys_to_duckdb(voter_id, election_id, enc_secret_key, public_key):
    try:
        conn = duckdb.connect("/duckdb/voter-keys.duckdb")
        print(f"inserting keys in duckdb for voter {voter_id}")
        conn.execute(f"INSERT INTO VoterKeys VALUES (?, ?, ?, ?)", (voter_id, election_id, base64.b64decode(enc_secret_key), base64.b64decode(public_key)))
    except Exception as e:
        print(f"error inserting keys in duckdb for voter {voter_id}: {e}")

# Sending ballot to Voting Server after receiving it in the Voting App frontend.
@app.post("/api/send-ballot")
async def send_ballot(voter_ballot: VoterBallot):
    print("Sending ballot to Voting Server")
    pyBallot: Ballot = await vote(voter_ballot.v, voter_ballot.lv_list, voter_ballot.election_id, voter_ballot.voter_id)
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post("http://vs_api:8000/receive-ballot", json=pyBallot.model_dump())
            response.raise_for_status()
            print(f"Ballot sent to voting server")
            # TODO: Get response from Voting server and then -> if status = validated return success to frontend, else return ballot invalid
            return {"status": "success"}
        except Exception as e:
            raise HTTPException(status_code=502, detail=f"Unable to send ballot to Voting Server: {e}")
            