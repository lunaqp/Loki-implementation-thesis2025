from fastapi import FastAPI
from bulletin_routes import router as bulletin_router
import base64
import duckdb
from contextlib import asynccontextmanager
from modelsVA import Ballot, VoterBallot
from vote_casting import vote, send_ballot_to_VS
from coloursVA import CYAN, RED, GREEN

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

    # Public and private keys are saved in internal duckdb database. Secret key is symmetrically encrypted with Fernet.
    save_keys_to_duckdb(voter_id, election_id, enc_secret_key, public_key)

    return {"status": "secret key received"}

def save_keys_to_duckdb(voter_id, election_id, enc_secret_key, public_key):
    try:
        conn = duckdb.connect("/duckdb/voter-keys.duckdb")
        print(f"{CYAN}inserting keys in duckdb for voter {voter_id}")
        conn.execute(f"INSERT INTO VoterKeys VALUES (?, ?, ?, ?)", (voter_id, election_id, base64.b64decode(enc_secret_key), base64.b64decode(public_key)))
    except Exception as e:
        print(f"{RED}error inserting keys in duckdb for voter {voter_id}: {e}")

# Sending ballot to Voting Server after receiving it in the Voting App frontend.
@app.post("/api/send-ballot")
async def send_ballot(voter_ballot: VoterBallot):
    # Constructing ballot
    pyBallot: Ballot = await vote(voter_ballot.v, voter_ballot.lv_list, voter_ballot.election_id, voter_ballot.voter_id)
    # Sending ballot to voting-server
    print(f"{GREEN}Sending ballot to Voting Server")
    await send_ballot_to_VS(pyBallot)