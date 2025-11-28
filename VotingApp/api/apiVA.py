from fastapi import FastAPI, HTTPException, Query
from bulletin_routes import router as bulletin_router
import duckdb
from contextlib import asynccontextmanager
from modelsVA import Ballot, VoterCastBallot, AuthRequest, Elections, IndexImageCBR
from vote_casting import vote, send_ballot_to_VS
from coloursVA import RED, GREEN, PURPLE, PINK
import httpx
from tally_verification import verify_tally
from fetch_functions_va import fetch_election_result_from_bb, fetch_candidates_names_from_bb, fetch_keys_from_ra, already_saved, fetch_ballot_from_bb
import time
import os
import save_to_duckdb as ddb
from datetime import datetime
from ballotVerification import verify_proof

BB_API_URL = os.environ.get("BB_API_URL")
RA_API_URL = os.environ.get("RA_API_URL")
VOTER_ID = os.environ.get("VOTER_ID")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialising DuckDB database:
    conn = duckdb.connect("/duckdb/voter-keys.duckdb")
    conn.sql("DROP TABLE IF EXISTS VoterKeys")
    conn.sql("DROP TABLE IF EXISTS VoterLogin")
    conn.sql("CREATE TABLE IF NOT EXISTS VoterKeys(VoterID INTEGER, ElectionID INTEGER, SecretKey BLOB, PublicKey BLOB)")
    conn.sql("CREATE TABLE IF NOT EXISTS VoterLogin(Username TEXT PRIMARY KEY, Password TEXT)")
    ddb.save_voter_login(VOTER_ID)
              
    yield  # yielding control back to FastAPI

app = FastAPI(lifespan=lifespan)

@app.get("/health")
def health():
    return{"ok": True}

# Register FastAPI router
app.include_router(bulletin_router)

@app.get("/api/election-result")
async def get_election_result(
    election_id: int = Query(..., description="ID of the election")):
    try:
        result = await fetch_election_result_from_bb(election_id)
        if not result or not getattr(result, "result", None):
            return {"electionid": election_id, "result": []}
        
        candidates = await fetch_candidates_names_from_bb(election_id)
        id_to_name = {c["id"]: c["name"] for c in candidates.get("candidates", [])} #map name to id

        #build dict to look up names by id, create new list from tally results adding each candidate name. 
        list_results = [
            {
                **r.model_dump(), 
                "candidate_name": id_to_name.get(
                    r.candidateid, f"Candidate {r.candidateid}"),
            }
            for r in result.result]

        return {
            "electionid": result.electionid,
            "result": list_results
        } 
    except Exception as e:
        print(f"Error combining result and candidate names: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

@app.get("/api/fetch-elections-for-voter")
async def fetch_elections_for_voter():
    print(f"address: {BB_API_URL}/send-elections-for-voter?voter_id={VOTER_ID}")
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{BB_API_URL}/send-elections-for-voter?voter_id={VOTER_ID}")
            response.raise_for_status() 

            elections: Elections = Elections.model_validate(response.json())
            
            print("fetching keys for elections associated with voter")
            # Retrieve keys for each election associated with voter. Avoid re-fetching by checking if election has been saved.
            for election in elections.elections:
                if already_saved(election.id):
                    continue
                else:
                    await fetch_keys_from_ra(VOTER_ID, election.id)

            return elections
    except Exception as e:
        print(f"{RED}Error fetching elections for voter {VOTER_ID}: {e}")
        raise HTTPException(status_code=500, detail=f"{RED}Error fetching elections for voter {VOTER_ID}: {str(e)}")     

@app.get("/api/fetch-cbr-images-for-voter")
async def fetch_elections_for_voter(
    election_id: int = Query(..., description="ID of the election"),
    voter_id: int = Query(..., description="ID of the voter")):
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{BB_API_URL}/cbr-for-voter?election_id={election_id}&voter_id={voter_id}")
            response.raise_for_status() 

            cbr_images: IndexImageCBR = IndexImageCBR.model_validate(response.json())
            
            return cbr_images
    except Exception as e:
        print(f"{RED}Error fetching cbr images for voter {voter_id}: {e}")
        raise HTTPException(status_code=500, detail=f"{RED}Error fetching cbr images for voter {voter_id}: {str(e)}")     


# Sending ballot to Voting Server after receiving it in the Voting App frontend.
@app.post("/api/send-ballot")
async def send_ballot(voter_ballot: VoterCastBallot):
    # Constructing ballot
    pyBallot: Ballot = await vote(voter_ballot.v, voter_ballot.lv_list, voter_ballot.election_id, VOTER_ID)
    # Sending ballot to voting-server
    print(f"{GREEN}Sending ballot to Voting Server")
    image_response = await send_ballot_to_VS(pyBallot) # Image response in format: {"image": image_filename.jpg}
    return image_response

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

@app.get("/api/fetch-election-dates")
async def fetch_elections_for_voter(
    election_id: int = Query(..., description="ID of the election")):
    try:
        async with httpx.AsyncClient() as client:
            payload = {"electionid": election_id} 
            response = await client.post(f"{BB_API_URL}/send-election-startdate", json = payload)
            response.raise_for_status() 

            election_dates = response.json()

            return election_dates
    except Exception as e:
        print(f"{RED}Error fetching election dates for election {election_id}: {e}")
        raise HTTPException(status_code=500, detail=f"{RED}Error fetching election dates for election {election_id}: {str(e)}")
    
@app.get("/api/verify_tally")
async def verify_election_tally(election_id: int = Query(..., description="ID of the election")):
    s_time_tally_verification = time.process_time_ns()
    verification_status = await verify_tally(election_id)
    e_time_tally_verification = time.process_time_ns() - s_time_tally_verification
    print(f"{PINK}Tallying verification time:", e_time_tally_verification/1000000, "ms")
    print(f"{PURPLE}Tally verification request received for election {election_id}. Verification status:", verification_status)
    return {"verified": verification_status}

@app.get("/api/verify-ballot")
async def verify_ballot(
    election_id: int = Query(..., description="ID of the election"),
    image_filename: str = Query(..., description="image associated with the ballot")
):
    ballot: Ballot = await fetch_ballot_from_bb(election_id, VOTER_ID, image_filename)
    if ballot == None:
        return {"status": "pending"}
    ballot_verified: bool = await verify_proof(election_id, VOTER_ID, ballot)

    return {"status": ballot_verified}
