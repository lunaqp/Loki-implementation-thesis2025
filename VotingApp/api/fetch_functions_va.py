"""Voting App fetch functiond.

This module contain network calls used by the Voting App to:

- Fetch the Bulletin Board election artifacts (params, voters, candidates,
  ballots, ballot ciphertexts, public keys, results).
- Fetch voter keys from the registration authority.

It also provides local DuckDB access to fetch key material.

All functions are written with FastAPI exceptions (``HTTPException``).
"""

import httpx
from fastapi import HTTPException
from coloursVA import RED
from modelsVA import ElGamalParams, ElectionResult, Ballot
from petlib.ec import EcPt, EcGroup, Bn
import base64
import duckdb
from pydantic import ValidationError
import os
import save_to_duckdb as ddb

RA_API_URL = os.environ.get("RA_API_URL")
"""Base URL for the Registration Authority API."""

BB_API_URL = os.environ.get("BB_API_URL")
"""Base URL for the Bulletin Board API."""

async def fetch_elgamal_params():
    """Fetch ElGamal parameters from the Bulletin Board.
    
    Returns:
        (GROUP, GENERATOR, ORDER) converted into petlib types.

    HTTPException:
        If BB cannot be reached or returns malformed data.
    """
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(f"{BB_API_URL}/elgamalparams")
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
            response = await client.get(f"{BB_API_URL}/candidates?election_id={election_id}")
            response.raise_for_status() 

            data = response.json()
            candidates_list: list = []

            for candidate in data["candidates"]:
                candidates_list.append(candidate["id"])
 
            return candidates_list
    except Exception as e:
        print(f"{RED}Error fetching candidates from BB: {e}")
        raise HTTPException(status_code=500, detail=f"{RED}Error fetching candidates from BB: {str(e)}")     

async def fetch_candidates_names_from_bb(election_id: int):
    """Fetch candidate names for an election from BB.

    Args:
        election_id: Election identifier.

    Returns:
        dict: Raw BB response JSON containing candidate data.

    HTTPException:
        If BB request fails.
    """
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{BB_API_URL}/candidates?election_id={election_id}"
            )
            resp.raise_for_status()
            data = resp.json()

            return data
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Error fetching candidates: {e}")

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
            response = await client.get(f"{BB_API_URL}/voters?election_id={election_id}")
            response.raise_for_status() 
          
            data = response.json()
            voters = data["voters"]
            voter_id_list = [v["id"] for v in voters]
          
            return voter_id_list
    except Exception as e:
        print(f"{RED}Error fetching voters from BB {e}")
        raise HTTPException(status_code=500, detail=f"{RED}Error fetching voters from BB: {str(e)}")


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
            response = await client.get(f"{BB_API_URL}/fetch_last_ballot_ctvs?election_id={election_id}")
            response.raise_for_status() 
          
            data = response.json()
            last_ballot_ctvs = data["last_ballot_ctvs"]
          
            return last_ballot_ctvs
    except Exception as e:
        print(f"{RED}Error fetching voters from BB {e}")
        raise HTTPException(status_code=500, detail=f"{RED}Error fetching voters from BB: {str(e)}")
    
async def fetch_election_result_from_bb(election_id):
    """Fetch the election result from BB (if available).

    Args:
        election_id: Election identifier.

    Returns:
        ElectionResult | None: election result if present; otherwise ``None``.

    HTTPException:
        If BB request fails.
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{BB_API_URL}/election-result?election_id={election_id}")
            if response.status_code == 404:
                return None
            response.raise_for_status() 
            data = response.json()
            if not data:
                return None
            try:
                election_result = ElectionResult.model_validate(data)
                return election_result
            except ValidationError as ve:
                print(f"Validation error for ElectionResult: {ve}")
                return None
    except Exception as e:
        print(f"{RED}Error fetching election result from BB {e}")
        raise HTTPException(status_code=500, detail=f"{RED}Error fetching election result from BB: {str(e)}")
    

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
            response = await client.get(f"{BB_API_URL}/public-keys-tsvs")
            response.raise_for_status() # gets http status code

            data: dict = response.json()
            public_key_ts_bin = base64.b64decode(data["publickey_ts"]) # recreates binary representation of key
            public_key_vs_bin = base64.b64decode(data["publickey_vs"])
            public_key_TS = EcPt.from_binary(public_key_ts_bin, GROUP) # recreates EcPt representation of key
            public_key_VS = EcPt.from_binary(public_key_vs_bin, GROUP)

            return public_key_TS, public_key_VS
    except Exception as e:
        print(f"{RED}Error fetching public keys for TS and VS {e}")

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
            response = await client.get(f"{BB_API_URL}/last_previous_last_ballot?election_id={election_id}&voter_id={voter_id}")
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
            response = await client.get(f"{BB_API_URL}/cbr_length?election_id={election_id}&voter_id={voter_id}")
            response.raise_for_status() 
            data = response.json()

        return data["cbr_length"]
    
    except Exception as e:
        print(f"{RED}Error fetching previous ballots from BB: {e}")
        raise HTTPException(status_code=500, detail=f"{RED}Error fetching previous ballots from BB: {str(e)}")    


def fetch_keys(voter_id, election_id):
    """Fetch a voter's secret/public keys from the local DuckDB.

    Args:
        voter_id: Voter identifier.
        election_id: Election identifier.

    Returns:
        tuple[bytes, bytes]: (secret_key, public_key) as raw bytes from DuckDB.
    """
    conn = duckdb.connect("/duckdb/voter-keys.duckdb")
    (secret_key, public_key) = conn.execute("""
            SELECT SecretKey, PublicKey
            FROM VoterKeys
            WHERE VoterID = ? AND ElectionID = ?
            """, (voter_id, election_id)).fetchone()

    return secret_key, public_key


async def fetch_keys_from_ra(voter_id, election_id):
    """Fetch a voter's keys from RA and persist them locally.

    Args:
        voter_id: Voter identifier.
        election_id: Election identifier.

    Returns:
        dict[str, str]: Status payload.

    HTTPException:
        If RA request fails.
    """
    print("fetching keys from RA...")
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{RA_API_URL}/voter-keys?voter_id={voter_id}&election_id={election_id}")
            response.raise_for_status() 

            data:dict = response.json()

            secret_key = data["secret_key"]
            public_key = data["public_key"]

            # Public and secret keys are saved in internal duckdb database.
            ddb.save_keys_to_duckdb(voter_id, election_id, secret_key, public_key)
            conn = duckdb.connect("/duckdb/voter-keys.duckdb")

            return {"status": "keys received"}
    except Exception as e:
        print(f"{RED}Error fetching keys for voter, {e}")
        raise HTTPException(status_code=500, detail=f"{RED}Error fetching keys for voter, {str(e)}")     

def already_saved(election_id):
    """Check whether keys for an election are already stored in DuckDB.

    Args:
        election_id: Election identifier.

    Returns:
        bool: ``True`` if at least one row exists for the election, otherwise ``False``.
    """
    conn = duckdb.connect("/duckdb/voter-keys.duckdb")
    result = conn.execute("""
        SELECT 1
        FROM VoterKeys
        WHERE ElectionID = ?
        LIMIT 1
    """, [election_id]).fetchone()

    return result is not None

async def fetch_ballot_from_bb(election_id, voter_id, image_filename):
    """Fetch a specific ballot from BB.

    Args:
        election_id: Election identifier.
        voter_id: Voter identifier.
        image_filename: Filename associated with the ballot.

    Returns:
        Ballot | None: Validated ``Ballot`` if present; otherwise ``None``.

    HTTPException:
        If BB request fails.
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{BB_API_URL}/ballot", params={
                    "election_id": election_id,
                    "voter_id": voter_id,
                    "image_filename": image_filename,
                })
            response.raise_for_status() 
            data = response.json()
            if data == None:
                return None
            # Recreating Pydantic ballot model
            ballot: Ballot = Ballot.model_validate(data)
           
            return ballot
    except Exception as e:
        print(f"{RED}Error fetching ballot election {election_id}, voter {voter_id} with image filename {image_filename}: {e}")
        raise HTTPException(status_code=500, detail=f"{RED}Error fetching ballot election {election_id}, voter {voter_id} with image filename {image_filename}: {str(e)}")
    
async def fetch_preceding_ballots_from_bb(election_id, voter_id, timestamp):
    """Fetch the immediately preceding ballots for a voter at a given timestamp.

    Args:
        election_id: Election identifier.
        voter_id: Voter identifier.
        timestamp: Timestamp used to query BB.

    Returns:
        tuple: ``(last_ballot_b64, previous_last_ballot_b64)`` where ``previous_last_ballot_b64`` is set to ``last_ballot_b64`` if BB reports it as ``None``.

    HTTPException:
        If BB request fails.
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{BB_API_URL}/preceding-ballots", params={
                    "election_id": election_id,
                    "voter_id": voter_id,
                    "timestamp": timestamp.isoformat(),
                })
            response.raise_for_status() 
            data = response.json()
            last_ballot_b64 = data["last_ballot"]
            previous_last_ballot_b64 = data["previous_last_ballot"]
            
            if  previous_last_ballot_b64 == None:
                previous_last_ballot_b64 = last_ballot_b64
                
            return last_ballot_b64, previous_last_ballot_b64
    except Exception as e:
        print(f"{RED}Error fetching ballot for election {election_id}, voter {voter_id} with timestamp {timestamp}: {e}")
        raise HTTPException(status_code=500, detail=f"{RED}Error fetching ballot for election {election_id}, voter {voter_id} with timestamp {timestamp}:  {str(e)}")
    