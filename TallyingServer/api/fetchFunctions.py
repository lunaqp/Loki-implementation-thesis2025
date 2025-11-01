from coloursTS import RED
from datetime import datetime
from fastapi import HTTPException
import httpx
import os
import base64
import json
from petlib.bn import Bn # For casting database values to petlib big integer types.

async def fetch_last_ballot_ctvs_from_bb(election_id):
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"http://bb_api:8000/fetch_last_ballot_ctvs?election_id={election_id}")
            response.raise_for_status() 
          
            data = response.json()
            last_ballot_ctvs = data["last_ballot_ctvs"]
          
            return last_ballot_ctvs
    except Exception as e:
        print(f"{RED}Error fetching voters from BB {e}")
        raise HTTPException(status_code=500, detail=f"{RED}Error fetching voters from BB: {str(e)}")
    

async def fetch_candidates_from_bb(election_id):
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"http://bb_api:8000/candidates?election_id={election_id}")
            response.raise_for_status() 
          
            data = response.json()
            candidates_list: list = []

            for candidate in data["candidates"]:
                candidates_list.append(candidate["id"])

            return candidates_list
    except Exception as e:
        print(f"{RED}Error fetching candidates from BB: {e}")
        raise HTTPException(status_code=500, detail=f"{RED}Error fetching candidates from BB: {str(e)}")     


async def fetch_voters_from_bb(election_id):
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"http://bb_api:8000/voters?election_id={election_id}")
            response.raise_for_status() 
          
            data = response.json()
            voters = data["voters"]
            voter_id_list = [v["id"] for v in voters]
          
            return voter_id_list
    except Exception as e:
        print(f"{RED}Error fetching voters from BB {e}")
        raise HTTPException(status_code=500, detail=f"{RED}Error fetching voters from BB: {str(e)}")


async def fetch_electiondates_from_bb(election_id):
    payload = {"electionid": election_id}
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post("http://bb_api:8000/send-election-startdate", json=payload)
            response.raise_for_status()

            election_start = datetime.fromisoformat(response.json().get("startdate")) # recreate datetime object from iso 8601 format.
            election_end = datetime.fromisoformat(response.json().get("enddate"))

        return election_start, election_end
    except Exception as e:
        print(f"{RED}Error fetching election start date: {e}")


def fetch_ts_secret_key():    
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    SECRET_KEY_PATH = os.path.join(BASE_DIR, 'keys.json')

    with open(SECRET_KEY_PATH, 'r') as file:
        data = json.load(file)
    
    sk_TS = Bn.from_binary(base64.b64decode(data["secret_key"]))

    return sk_TS

