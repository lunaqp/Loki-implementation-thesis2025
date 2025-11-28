import requests #requests is the HTTP client used to call BB/request GET
import os 
from fastapi import APIRouter, HTTPException

# Equivalent of Flask Blueprint
router = APIRouter(
    prefix="/api/bulletin",  # same as url_prefix in Flask
    tags=["bulletin"]
)

#This reads BB URL from the env
BB_API_URL = os.environ.get("BB_API_URL") # Docker container addresses and envrionment variables defined in docker-compose.yml

@router.get("/candidates") #define route in VotingApp
def get_candidates(election_id):
    try:
        resp = requests.get(f"{BB_API_URL}/candidates?election_id={election_id}", timeout=5) #Make GET call to BB /candidates endpoint
        resp.raise_for_status()
        return resp.json() #forwared JSON to front end
    except requests.exceptions.RequestException as e: #catch network errors
        raise HTTPException(status_code=500, detail=str(e))
        