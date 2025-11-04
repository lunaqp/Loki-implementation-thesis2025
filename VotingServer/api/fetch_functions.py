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

async def fetch_electiondates_from_bb(election_id):
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

# TODO: Find a good place to store params to avoid excessive database calls.
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

async def fetch_voter_public_key_from_bb(voter_id, election_id):
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

