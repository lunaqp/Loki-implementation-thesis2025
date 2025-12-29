"""
Voting App backend service.

This module implements the FastAPI backend for the Voting App used by
individual voters. It provides endpoints for:

- Fetching elections and election metadata for a voter.
- Casting and submitting ballots to the Voting Server (VS).
- Fetching Cast Ballot Record (CBR) images and indices.
- Authenticating voters.
- Fetching and verifying election results against cryptographic proofs.
- Verifying individual ballots against their cryptographic proof.

The service coordinates with multiple external components, including:
- Bulletin Board (BB).
- Voting Server (VS).
- Registration Authority (RA).

Local DuckDB storage is used to persist voter credentials and cryptographic keys.
"""
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
from ballotVerification import verify_proof

# Fetch environment variables for communication with BackendSystems and for voter identification.
BB_API_URL = os.environ.get("BB_API_URL")
RA_API_URL = os.environ.get("RA_API_URL")
VOTER_ID = os.environ.get("VOTER_ID")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    FastAPI lifespan handler for application startup and shutdown.

    Initializes the DuckDB database used for storing voter keys and login data,
    and inserts the voter's login credentials on startup.
    """
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
    """Return status response indicating the service is running."""
    return{"ok": True}

# Register FastAPI router
app.include_router(bulletin_router)

@app.get("/api/election-result")
async def get_election_result(
    election_id: int = Query(..., description="ID of the election")):
    """
    Fetch and return the final election result with candidate names.

    Combines tally results from the Bulletin Board with candidate metadata
    to return a human-readable election result.

    Args:
        election_id (int): Identifier of the election.

    Returns:
        dict: Election result with candidate names and vote counts.
    """
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
    """
    Fetch all elections associated with the authenticated voter.

    For each election, cryptographic keys are fetched from the Registration
    Authority if they have not already been stored locally.

    Returns:
        Elections: Elections associated with the voter.
    """
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
    """
    Fetch  index, image, and timestamp for all ballots on a voter's Cast Ballot Record (CBR).

    Args:
        election_id (int): Identifier of the election.
        voter_id (int): Identifier of the voter.

    Returns:
        IndexImageCBR: List of index, image, and timestamp for all ballots on a voter's CBR.
    """
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
    """
    Ballot is constructed from the data sent from Voting App frontend.
    The resulting ballot is sent to the Voting Server.

    The voting server returns a image path-reference for the image that
    needs to be remembered as the memorable information associated with
    the just cast ballot.

    Args:
        voter_ballot (VoterCastBallot): Vote selections and election ID.

    Returns:
        dict: Image metadata associated with the submitted ballot.
    """
    s_time_vote_incl_network = time.process_time_ns() # Performance testing: Start timer for voting including network calls

    # Constructing ballot
    pyBallot: Ballot = await vote(voter_ballot.v, voter_ballot.lv_list, voter_ballot.election_id, VOTER_ID)

    e_time_vote_incl_network = time.process_time_ns() - s_time_vote_incl_network
    print(f"{PINK}Ballot vote time including network calls:", e_time_vote_incl_network/1000000, "ms")

    # Sending ballot to voting-server
    print(f"{GREEN}Sending ballot to Voting Server")
    image_response = await send_ballot_to_VS(pyBallot) # Image response in format: {"image": image_filename.jpg}

    return image_response

@app.post("/api/user-authentication")
def authenticate_user(auth: AuthRequest):
    """
    Authenticate a voter using locally stored credentials.

    Args:
        auth (AuthRequest): Provided username and password.

    Returns:
        dict: Authentication status.
    """
    try:
        conn = duckdb.connect("/duckdb/voter-keys.duckdb")
        result = conn.execute("""
                SELECT Password
                FROM VoterLogin
                WHERE Username = ?
                """, (auth.provided_username,)).fetchone() # Username and password hardcoded for prototype purposes as username = voter<id> and password = pass<id>.
                                                           # voterid = 1 -> username = voter1, password = pass1

        if not result:
            return {"authenticated": False}
        
        password = result[0]
        return {"authenticated": auth.provided_password == password}
    
    except Exception as e:
        return {"authenticated": False}

@app.get("/api/fetch-election-dates")
async def fetch_elections_for_voter(
    election_id: int = Query(..., description="ID of the election")):
    """
    Fetch start and end dates for a given election.

    Args:
        election_id (int): Identifier of the election.

    Returns:
        dict: Election start and end dates.
    """
    try:
        async with httpx.AsyncClient() as client:
            payload = {"electionid": election_id} 
            response = await client.post(f"{BB_API_URL}/send-election-startdate", json = payload)
            response.raise_for_status() 

            election_dates = response.json()
            print("type of election_dates: ", type(election_dates))
            return election_dates
    except Exception as e:
        print(f"{RED}Error fetching election dates for election {election_id}: {e}")
        raise HTTPException(status_code=500, detail=f"{RED}Error fetching election dates for election {election_id}: {str(e)}")
    
@app.get("/api/verify_tally")
async def verify_election_tally(election_id: int = Query(..., description="ID of the election")):
    """
    Verifies the result of the tally as calculated by the Tallying Server.
    Runs verification locally.

    Args:
        election_id (int): Identifier of the election.

    Returns:
        dict: Verification status. True if verification succeeds, False if verification fails.
    """
    s_time_tally_verification = time.process_time_ns() # Performance testing - tally verification
    verification_status = await verify_tally(election_id)
    e_time_tally_verification = time.process_time_ns() - s_time_tally_verification  # Performance testing - tally verification
    print(f"{PINK}Tallying verification time:", e_time_tally_verification/1000000, "ms")
    print(f"{PURPLE}Tally verification request received for election {election_id}. Verification status:", verification_status)
    return {"verified": verification_status}

@app.get("/api/verify-ballot")
async def verify_ballot(
    election_id: int = Query(..., description="ID of the election"),
    image_filename: str = Query(..., description="image associated with the ballot")
):
    """
    Verifies correct construction of the ballot by running verification locally.

    Args:
        election_id (int): Identifier of the election.
        image_filename (string): Filename of image associated with ballot.

    Returns:
        dict: Verification status. True if verification succeeds, False if verification fails.
    """
    ballot: Ballot = await fetch_ballot_from_bb(election_id, VOTER_ID, image_filename)
    if ballot == None:
        return {"status": "pending"}
    s_time_verify_incl_network = time.process_time_ns() # Performance testing: Start timer for ballot verification including network calls
    ballot_verified: bool = await verify_proof(election_id, VOTER_ID, ballot)
    e_time_verify_incl_network = time.process_time_ns() - s_time_verify_incl_network
    print(f"{PINK}Ballot verification time including network calls:", e_time_verify_incl_network/1000000, "ms")

    return {"status": ballot_verified}
