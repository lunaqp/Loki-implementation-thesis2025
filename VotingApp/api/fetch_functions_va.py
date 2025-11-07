import httpx
from fastapi import HTTPException
from coloursVA import RED
from modelsVA import ElGamalParams, ElectionResult
from petlib.ec import EcPt, EcGroup, Bn
import base64
import duckdb
import os
from cryptography.fernet import Fernet
from pydantic import ValidationError

async def fetch_elgamal_params():
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

async def fetch_candidates_names_from_bb(election_id: int):
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"http://bb_api:8000/candidates?election_id={election_id}"
            )
            resp.raise_for_status()
            data = resp.json()

            return data
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Error fetching candidates: {e}")

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
    
async def fetch_election_result_from_bb(election_id):
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"http://bb_api:8000/election-result?election_id={election_id}")
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

async def fetch_last_and_previouslast_ballot_from_bb(voter_id, election_id):
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
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"http://bb_api:8000/cbr_length?election_id={election_id}&voter_id={voter_id}")
            response.raise_for_status() 
            data = response.json()

        return data["cbr_length"]
    
    except Exception as e:
        print(f"{RED}Error fetching previous ballots from BB: {e}")
        raise HTTPException(status_code=500, detail=f"{RED}Error fetching previous ballots from BB: {str(e)}")    


def fetch_keys(voter_id, election_id):
    conn = duckdb.connect("/duckdb/voter-keys.duckdb")
    (enc_secret_key, public_key) = conn.execute("""
            SELECT SecretKey, PublicKey
            FROM VoterKeys
            WHERE VoterID = ? AND ElectionID = ?
            """, (voter_id, election_id)).fetchone()
    #usk_bin = decrypt_key(enc_secret_key)
    usk_bin = enc_secret_key

    return usk_bin, public_key


def decrypt_key(enc_secret_key):
    ENCRYPTION_KEY = os.getenv("VOTER_SK_DECRYPTION_KEY") # Symmetric key - saved in docker-compose.yml
    cipher = Fernet(ENCRYPTION_KEY)
    decrypted_secret_key = cipher.decrypt(enc_secret_key)
    print(f"decrypted secret key = {decrypted_secret_key}")
    return decrypted_secret_key