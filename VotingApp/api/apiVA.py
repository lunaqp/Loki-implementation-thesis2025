from fastapi import FastAPI, HTTPException, Query
from bulletin_routes import router as bulletin_router
import base64
import duckdb
from contextlib import asynccontextmanager
from modelsVA import Ballot, VoterBallot, AuthRequest, Elections, IndexImageCBR
from vote_casting import vote, send_ballot_to_VS
from coloursVA import CYAN, RED, GREEN
import httpx

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialising DuckDB database:
    conn = duckdb.connect("/duckdb/voter-keys.duckdb")
    conn.sql("CREATE TABLE VoterKeys(VoterID INTEGER, ElectionID INTEGER, SecretKey BLOB, PublicKey BLOB)")
    conn.sql("CREATE TABLE VoterLogin(Username TEXT PRIMARY KEY, Password TEXT)")
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

@app.get("/api/fetch-elections-for-voter")
async def fetch_elections_for_voter(
    voter_id: int = Query(..., description="ID of the voter")):
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"http://bb_api:8000/send-elections-for-voter?voter_id={voter_id}")
            response.raise_for_status() 

            elections: Elections = Elections.model_validate(response.json())
            
            return elections
    except Exception as e:
        print(f"{RED}Error fetching elections for voter {voter_id}: {e}")
        raise HTTPException(status_code=500, detail=f"{RED}Error fetching elections for voter {voter_id}: {str(e)}")     

@app.get("/api/fetch-cbr-images-for-voter")
async def fetch_elections_for_voter(
    election_id: int = Query(..., description="ID of the election"),
    voter_id: int = Query(..., description="ID of the voter")):
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"http://bb_api:8000/cbr-for-voter?election_id={election_id}&voter_id={voter_id}")
            response.raise_for_status() 

            cbr_images: IndexImageCBR = IndexImageCBR.model_validate(response.json())
            
            return cbr_images
    except Exception as e:
        print(f"{RED}Error fetching cbr images for voter {voter_id}: {e}")
        raise HTTPException(status_code=500, detail=f"{RED}Error fetching cbr images for voter {voter_id}: {str(e)}")     


@app.post("/receive-keys")
def receive_secret_key(data: dict):
    voter_id = data["voter_id"]
    election_id = data["election_id"]
    enc_secret_key = data["secret_key"]
    public_key = data["public_key"]

    # Public and private keys are saved in internal duckdb database. Secret key is symmetrically encrypted with Fernet.
    save_keys_to_duckdb(voter_id, election_id, enc_secret_key, public_key)
    save_voter_login(voter_id)

    return {"status": "secret key received"}

def save_keys_to_duckdb(voter_id, election_id, enc_secret_key, public_key):
    try:
        conn = duckdb.connect("/duckdb/voter-keys.duckdb")
        print(f"{CYAN}inserting keys in duckdb for voter {voter_id}")
        conn.execute(f"INSERT INTO VoterKeys VALUES (?, ?, ?, ?)", (voter_id, election_id, base64.b64decode(enc_secret_key), base64.b64decode(public_key)))
        conn.table("VoterKeys").show() 
    except Exception as e:
        print(f"{RED}error inserting keys in duckdb for voter {voter_id}: {e}")

def save_voter_login(voter_id):
    username = f"voter{voter_id}"
    password = f"pass{voter_id}"
    try:
        conn = duckdb.connect("/duckdb/voter-keys.duckdb")
        print(f"{CYAN}inserting login info in duckdb for voter {voter_id}")
        conn.execute(f"INSERT INTO VoterLogin (Username, Password) VALUES (?, ?) ON CONFLICT(Username) DO NOTHING", (username, password))
        conn.table("VoterLogin").show() 
    except Exception as e:
        print(f"{RED}error inserting login info in duckdb for voter {voter_id}: {e}")

# Sending ballot to Voting Server after receiving it in the Voting App frontend.
@app.post("/api/send-ballot")
async def send_ballot(voter_ballot: VoterBallot):
    # Constructing ballot
    pyBallot: Ballot = await vote(voter_ballot.v, voter_ballot.lv_list, voter_ballot.election_id, voter_ballot.voter_id)
    # Sending ballot to voting-server
    print(f"{GREEN}Sending ballot to Voting Server")
    await send_ballot_to_VS(pyBallot)

@app.post("/api/user-authentication")
def authenticate_user(auth: AuthRequest):
    try:
        conn = duckdb.connect("/duckdb/voter-keys.duckdb")
        result = conn.execute("""
                SELECT Password
                FROM VoterLogin
                WHERE Username = ?
                """, (auth.provided_username,)).fetchone() # Username is voterid for prototype purposes.

        if not result:
            return {"authenticated": False}
        
        password = result[0]
        return {"authenticated": auth.provided_password == password}
    
    except Exception as e:
        return {"authenticated": False}
