"""
FastAPI router for Bulletin Board proxy endpoint fetching candidates in an
election.
"""
import requests #requests is the HTTP client used to call BB/request GET
import os 
from fastapi import APIRouter, HTTPException

# Router for the Bulletin Board.
router = APIRouter(
    prefix="/api/bulletin", 
    tags=["bulletin"]
)

# This reads BB URL from the environment
BB_API_URL = os.environ.get("BB_API_URL") # Docker container addresses and envrionment variables defined in docker-compose.yml

@router.get("/candidates") #define route in VotingApp
def get_candidates(election_id):
    """
    Retrieve the list of candidates for a given election.

    This endpoint forwards the request to the Bulletin Board service and
    returns the response JSON directly to the client.

    Args:
        election_id: Identifier of the election.

    Returns:
        dict: JSON response containing candidate information (id and name).

    Raises:
        HTTPException: If the Bulletin Board request fails or times out.
    """
    try:
        resp = requests.get(f"{BB_API_URL}/candidates?election_id={election_id}", timeout=5) # Make GET call to BB /candidates endpoint
        resp.raise_for_status()
        return resp.json() # Forward JSON to front end
    except requests.exceptions.RequestException as e: # Catch network errors
        raise HTTPException(status_code=500, detail=str(e))
        