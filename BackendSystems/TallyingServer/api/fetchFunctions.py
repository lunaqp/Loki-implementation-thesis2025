"""BB fetch functions for the Tallying Server.

This module contains network calls used by the tallying logic:
- Fetch ElGamal parameters from BB and convert them into petlib types.
- Fetch election artifacts (voters, candidates, ciphertexts, dates) from BB.
- Fetch TS secret key from local storage.

All fetch functions use ``httpx.AsyncClient`` and raise FastAPI ``HTTPException``.
"""

from coloursTS import RED
from datetime import datetime
from fastapi import HTTPException
import httpx
import os
import base64
import json
from petlib.bn import Bn # For casting database values to petlib big integer types.
from petlib.ec import EcGroup, EcPt, EcGroup
from modelsTS import ElGamalParams

async def fetch_elgamal_params():
    """Fetch ElGamal parameters from the Bulletin Board.
    
    Returns:
        (GROUP, GENERATOR, ORDER) converted into petlib types.

    HTTPException:
        If BB cannot be reached or returns malformed data.
    """
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get("http://bb_api:8000/elgamalparams")
            data = resp.json()
            params = ElGamalParams(
                group = data["group"],
                generator = data["generator"],
                order = data["order"]
            )

            # Convert to proper types for cryptographic functions.
            GROUP = EcGroup(params.group)
            GENERATOR = EcPt.from_binary(base64.b64decode(params.generator), GROUP)
            ORDER = Bn.from_binary(base64.b64decode(params.order))
            
            return GROUP, GENERATOR, ORDER
        
        except Exception as e:
            raise HTTPException(status_code=502, detail=f"Unable to fetch elgamal params: {e}")


async def fetch_last_ballot_ctvs_from_bb(election_id):
    """Fetch the last ciphertext vote (ctv) from BB per voter in election.

    Args:
    election_id: Election identifier.

    Returns:
        list: The value of ``last_ballot_ctvs`` returned by BB.

    HTTPException:
        If BB request fails.
    """
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
    """Fetch candidates for an election from BB.

    Args:
        election_id: Election identifier.

    Returns:
        list[int]: Candidate id list.

    HTTPException:
        If BB request fails.
    """
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
    """Fetch voter ids for an election from BB.

    Args:
        election_id: Election identifier.

    Returns:
        list[int]: Voter id list.

    HTTPException<.
        If BB request fails.
    """
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
    """Fetch election start/end datetimes from BB.

    Args:
        election_id: Election identifier.

    Returns:
        tuple[datetime, datetime]: (election_start, election_end) parsed from ISO-8601 strings.

    HTTPException:
        If BB request fails or returns invalid timestamps.
    """
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
    """Fetch the TS secret key from local ``keys.json``.
    Assumes a ``keys.json`` file adjacent to this module containing a base64-encoded ``secret_key`` field.

    Returns:
        Bn: TS secret key as a petlib big integer.
    """
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    SECRET_KEY_PATH = os.path.join(BASE_DIR, 'keys.json')

    with open(SECRET_KEY_PATH, 'r') as file:
        data = json.load(file)
    
    sk_TS = Bn.from_binary(base64.b64decode(data["secret_key"]))

    return sk_TS

