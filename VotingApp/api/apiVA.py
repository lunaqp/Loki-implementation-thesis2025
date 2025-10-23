#To run -> npm run api
from fastapi import FastAPI
import os
from bulletin_routes import router as bulletin_router
import base64
import duckdb
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialising DuckDB database:
    conn = duckdb.connect("/duckdb/voter-secret-keys.duckdb")
    conn.sql("CREATE TABLE VoterSecretKeys(VoterID INTEGER, ElectionID INTEGER, Key BLOB)")
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

@app.post("/receive-secret-key")
def receive_secret_key(data: dict):
    voter_id = data["voter_id"]
    election_id = data["election_id"]
    enc_secret_key = data["secret_key"]
    print(f"voterid: {voter_id}, electionid: {election_id}, secretkey: {enc_secret_key}")
    print(f"secret key decoded: {base64.b64decode(enc_secret_key)}")

    # TODO: Figure out where to save secret keys/how to store.
    save_secret_key_to_duckdb(voter_id, election_id, enc_secret_key)

    return {"status": "secret key received"}

def save_secret_key_to_duckdb(voter_id, election_id, enc_secret_key):
    try:
        conn = duckdb.connect("/duckdb/voter-secret-keys.duckdb")
        print(f"inserting secret key in duckdb for voter {voter_id}")
        conn.execute(f"INSERT INTO VoterSecretKeys VALUES (?, ?, ?)", (voter_id, election_id, enc_secret_key))
    except Exception as e:
        print(f"error inserting secret key in duckdb for voter {voter_id}: {e}")