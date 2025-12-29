"""Voting Server fetch functions.

This module provides asynchronous helpers for retrieving election data
from the bulletin board and local state from DuckDB. 
- Fetch election start/end timestamps.
- Fetch ElGamal parameters and convert them to petlib types.
- Fetch voters, candidates, and public keys.
- Fetch ballot-related metadata.
- Fetch image filenames from the local DuckDB.

BB endpoints return binary objects (keys, ciphertexts) as base64 strings.
Concurrency around DuckDB access is protected with ``duckdb_lock``.
"""

from datetime import datetime
import httpx
from coloursVS import RED
from fastapi import HTTPException
import base64
from petlib.ec import EcPt
from modelsVS import ElGamalParams
import httpx
import base64
from petlib.bn import Bn # For casting database values to petlib big integer types.
from petlib.ec import EcGroup, EcPt, EcGroup
import duckdb
from lock import duckdb_lock

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
            response.raise_for_status() # gets http status code

            election_start = datetime.fromisoformat(response.json().get("startdate")) # recreate datetime object from iso 8601 format.
            election_end = datetime.fromisoformat(response.json().get("enddate"))

        return election_start, election_end
    except Exception as e:
        print(f"{RED}Error fetching election start date: {e}")

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
            raise HTTPException(status_code=502, detail=f"{RED}Unable to fetch elgamal params: {e}") #NOTE: What would be the most correct status_codes for different scenarios?



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

async def fetch_public_keys_from_bb():
    """Fetch TS and VS public keys from BB.

    Returns:
        tuple[EcPt, EcPt]: (public_key_ts, public_key_vs) as petlib EC points.

    HTTPException:
        If parameters/keys cannot be fetched or decoded.
    """
    GROUP, _, _ = await fetch_elgamal_params()
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get("http://bb_api:8000/public-keys-tsvs")
            response.raise_for_status() # gets http status code

            data: dict = response.json()
            public_key_ts_bin = base64.b64decode(data["publickey_ts"]) # recreates binary representation of key
            public_key_vs_bin = base64.b64decode(data["publickey_vs"])
            public_key_TS = EcPt.from_binary(public_key_ts_bin, GROUP) # recreates EcPt representation of key
            public_key_VS = EcPt.from_binary(public_key_vs_bin, GROUP)

            return public_key_TS, public_key_VS
    except Exception as e:
        print(f"{RED}Error fetching public keys for TS and VS {e}")

async def fetch_voter_public_key_from_bb(voter_id, election_id):
    """Fetch a voter's public key from BB.

    Args:
        voter_id: Voter identifier.
        election_id: Election identifier.

    Returns:
        bytes: Raw public key bytes decoded from base64.

    HTTPException:
        If BB request fails.
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"http://bb_api:8000/voter-public-key?election_id={election_id}&voter_id={voter_id}")
            response.raise_for_status() 
          
            data = response.json()
            voter_public_key_bin = base64.b64decode(data["voter_public_key"])
            
            return voter_public_key_bin
    except Exception as e:
        print(f"{RED}Error fetching public key for voter: {e}")
        raise HTTPException(status_code=500, detail=f"{RED}Error fetching public key for voter:  {str(e)}")     

async def fetch_ballot_hash_from_bb(election_id):
    """Fetch all ballot hashes for an election from BB.

    Args:
        election_id: Election identifier.

    Returns:
        list: List of ballot hashes.

    HTTPException:
        If BB request fails.
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"http://bb_api:8000/fetch-ballot-hashes?election_id={election_id}")
            response.raise_for_status() 
          
            data = response.json()
            ballothash_list = data["ballot_hashes"]
            
            return ballothash_list
    except Exception as e:
        print(f"{RED}Error fetching list of all ballot hashes")
        raise HTTPException(status_code=500, detail=f"{RED}Error fetching list of all ballot hashes:  {str(e)}")     

async def fetch_last_and_previouslast_ballot_from_bb(election_id, voter_id):
    """Fetch the last and previous-to-last ballot for a voter from BB.

    Args:
        election_id: Election identifier.
        voter_id: Voter identifier.

    Returns:
        tuple[object, object]: (last_ballot_b64, previous_last_ballot_b64) as provided by BB.

    HTTPException:
        If BB request fails.
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"http://bb_api:8000/last_previous_last_ballot?election_id={election_id}&voter_id={voter_id}")
            response.raise_for_status() 

            data = response.json()
            last_ballot_b64 = data["last_ballot"]
            previous_last_ballot_b64 = data["previous_last_ballot"]

            return last_ballot_b64, previous_last_ballot_b64
    except Exception as e:
        print(f"{RED}Error fetching previous ballots from BB: {e}")
        raise HTTPException(status_code=500, detail=f"{RED}Error fetching previous ballots from BB: {str(e)}")     


async def fetch_cbr_length_from_bb(voter_id, election_id):
    """Fetch the current CBR length for a voter in an election from BB.

    Args:
        voter_id: Voter identifier.
        election_id: Election identifier.

    Returns:
        int: CBR length as returned by BB.

    HTTPException:
        If BB request fails.
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"http://bb_api:8000/cbr_length?election_id={election_id}&voter_id={voter_id}")
            response.raise_for_status() 
            data = response.json()

        return data["cbr_length"]
    
    except Exception as e:
        print(f"{RED}Error fetching previous ballots from BB: {e}")
        raise HTTPException(status_code=500, detail=f"{RED}Error fetching previous ballots from BB: {str(e)}")    

async def fetch_image_filename(election_id, voter_id):
    """Fetch the next unprocessed image filename for a voter from VS DuckDB.

    This queries the VS-local database for the oldest unprocessed timestamp entry.

    Args:
        election_id: Election identifier.
        voter_id: Voter identifier.

    Returns:
        str | None: Image path/filename if available; otherwise ``None``.

    Access is protected by ``duckdb_lock`` to avoid concurrent DuckDB usage.
    """
    try:
        async with duckdb_lock: # lock is acquired to check if access should be allowed, lock while accessing ressource and is then released before returning  
            conn = duckdb.connect("/duckdb/voter-data.duckdb")
            (image_filename,) = conn.execute("""
                    SELECT ImagePath
                    FROM VoterTimestamps
                    WHERE VoterID = ? AND ElectionID = ? AND Processed = false
                    ORDER BY Timestamp ASC
                    LIMIT 1
                    """, (voter_id, election_id)).fetchone()
        return image_filename
    except Exception as e:
        print(f"{RED}error fetching timestamp from duckdb for voter {voter_id} in election {election_id}: {e}")


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
            response.raise_for_status() # gets http status code

            election_start = datetime.fromisoformat(response.json().get("startdate")) # recreate datetime object from iso 8601 format.
            election_end = datetime.fromisoformat(response.json().get("enddate"))

        return election_start, election_end
    except Exception as e:
        print(f"{RED}Error fetching election start date: {e}")