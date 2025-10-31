from zksk import Secret, base, DLRep
from petlib.bn import Bn # For casting database values to petlib big integer types.
from petlib.ec import EcPt
from zksk import Secret, DLRep
import httpx
from fastapi import HTTPException
from coloursTS import RED
from keygen import get_elgamal_params
import os
import json
import base64

# Fetching last ballot for each voter:

#last_ballots = [sublist[-1][0] for sublist in CBR]

# Calling the tallying function:
#votes, nizk=tally(g,order,sk_T, last_ballots,candidates,voters)

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


# Tally function:
async def tally(election_id):
    _, GENERATOR, ORDER = await get_elgamal_params()
    candidates = await fetch_candidates_from_bb(election_id)
    candidates_length = len(candidates)
    voters = len(await fetch_voters_from_bb(election_id))
    sk_TS = fetch_ts_secret_key
    last_ballots_ctvs_b64: list = await fetch_last_ballot_ctvs_from_bb(election_id)
    last_ballots_ctvs = convert_to_ecpt(last_ballots_ctvs_b64)
    print(f" Last ballot ctvs: {last_ballots_ctvs}")

    sk=Secret(value=sk_TS)
    stmt, nizk=[], []
    votes_for_candidate=[0]*candidates_length
    
    for i in range(candidates_length):
        c0, c1 =(0*GENERATOR), (0*GENERATOR)

        #summing up all encrypted votes for a candidate
        for j in range(voters):
            c0+= 1 #ballots[j][i][0]
            c1+= 1 #ballots[j][i][1]
        sum_votes=dec((c0,c1), sk_TS)

        #finding the number of votes for a candidate
        for j in range(voters):
            if sum_votes==j*GENERATOR:
                votes_for_candidate[i]=j
                break

        print("Votes for Candidate",i+1,":", votes_for_candidate[i])
        #print("Votes for Candidate", candidates[i]["id"],":", votes_for_candidate[i])

        #constructing the statement for the ZK proof
        stmt.append(stmt_tally(GENERATOR, ORDER, j, c0, c1, sk))

        #proving the statement
        nizk.append(stmt[-1].prove({sk: sk.value}))

    print("Abstention votes:", voters-sum(votes_for_candidate)) 
    return votes_for_candidate, nizk

# Tally statement:
def stmt_tally(generator, order, votes, c0, c1, sk_TS):
    one=Secret(value=1)
    neg_c0 = (-1)*c0
    return DLRep(votes*generator, one*c1 + sk_TS*neg_c0)

def dec(ct, sk):
    c0, c1 = ct
    message = (c1 + (-sk*c0))

    return message


def fetch_ts_secret_key():    
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    SECRET_KEY_PATH = os.path.join(BASE_DIR, 'keys.json')

    with open(SECRET_KEY_PATH, 'r') as file:
        data = json.load(file)
    
    sk_VS = Bn.from_binary(base64.b64decode(data["secret_key"]))

    return sk_VS

def convert_to_ecpt(ctv_list, GROUP):
    # Converting to binary
    ctv_bin = []
    for ctvs in ctv_list: # for each voter ctv-list
        decoded_pairs = []
    for ct0, ct1 in ctvs: # for the ciphertext pairs for each candidate
        decoded_pairs.append((base64.b64decode(ct0), base64.b64decode(ct1)))
    ctv_bin.append(decoded_pairs)

    # Converting to ecpt
    ctv_ecpt = []
    for ctvs in ctv_bin: # for each voter ctv-list
        decoded_pairs = []
    for ct0, ct1 in ctvs: # for the ciphertext pairs for each candidate
        decoded_pairs.append((EcPt.from_binary(ct0, GROUP), EcPt.from_binary(ct1, GROUP)))
    ctv_ecpt.append(decoded_pairs)
    
    return ctv_ecpt
