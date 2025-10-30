from modelsVS import Ballot
import os
from zksk import Secret, base
from petlib.bn import Bn # For casting database values to petlib big integer types.
from petlib.ec import EcPt
from statement import stmt
from keygen import get_elgamal_params
import httpx
from fastapi import HTTPException
import base64
from hashVS import hash_ballot
import json

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
        print(f"Error fetching voters from BB {e}")
        raise HTTPException(status_code=500, detail=f"Error fetching voters from BB: {str(e)}")     

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
        print(f"Error fetching candidates from BB: {e}")
        raise HTTPException(status_code=500, detail=f"Error fetching candidates from BB: {str(e)}")     

async def fetch_public_keys_from_bb():
    GROUP, _, _ = await get_elgamal_params()
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
        print(f"Error fetching public keys for TS and VS {e}")

async def fetch_voter_public_key_from_bb(voter_id, election_id):
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"http://bb_api:8000/voter-public-key?election_id={election_id}&voter_id={voter_id}")
            response.raise_for_status() 
          
            data = response.json()
            voter_public_key_bin = base64.b64decode(data["voter_public_key"])
            
            return voter_public_key_bin
    except Exception as e:
        print(f"Error fetching public key for voter: {e}")
        raise HTTPException(status_code=500, detail=f"Error fetching public key for voter:  {str(e)}")     

async def fetch_ballot_hash_from_bb(election_id):
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"http://bb_api:8000/fetch-ballot-hashes?election_id={election_id}")
            response.raise_for_status() 
          
            data = response.json()
            ballothash_list = data["ballot_hashes"]
            
            return ballothash_list
    except Exception as e:
        print(f"Error fetching list of all ballot hashes")
        raise HTTPException(status_code=500, detail=f"Error fetching list of all ballot hashes:  {str(e)}")     

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
        print(f"Error fetching previous ballots from BB: {e}")
        raise HTTPException(status_code=500, detail=f"Error fetching previous ballots from BB: {str(e)}")     


async def fetch_cbr_length_from_bb(voter_id, election_id):
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"http://bb_api:8000/cbr_length?election_id={election_id}&voter_id={voter_id}")
            response.raise_for_status() 
            data = response.json()

        return data["cbr_length"]
    
    except Exception as e:
        print(f"Error fetching previous ballots from BB: {e}")
        raise HTTPException(status_code=500, detail=f"Error fetching previous ballots from BB: {str(e)}")    


async def validate_ballot(pyballot:Ballot):
    election_id = pyballot.electionid
    ballot_hash: list = await fetch_ballot_hash_from_bb(election_id) #NOTE Do we need compare the hash of the new ballot with all ballot hashes in an election or only the ballot hashes for that voter id. ot whole BB
    voter_list: list = await fetch_voters_from_bb(election_id)

    hashed_ballot = hash_ballot(pyballot) #hash the ballot
    uid_exists = False
    ballot_not_included = False
    proof_verified = False

    for id in voter_list:
        if pyballot.voterid == id:
            uid_exists = True

    if not ballot_hash: # Guarding against empty list, not necessary if we dont have to validate Ballot0
        ballot_not_included = True

    if hashed_ballot not in ballot_hash:
        ballot_not_included = True

    proof_verified = await verify_proof(election_id, pyballot.voterid, pyballot)
    #proof_verified = True #for testing purposes, keep above instead.

    ballot_validated = uid_exists and ballot_not_included and proof_verified

    return ballot_validated

    #NOTE Function to create the hash value in RA missing.

async def verify_proof(election_id, voter_id, pyballot):
    GROUP, GENERATOR, _, cbr_length, candidates, pk_TS, pk_VS = await fetch_data(election_id, voter_id)

    current_ballot_b64 = (pyballot.ctv, pyballot.ctlv, pyballot.ctlid, pyballot.proof)
    ctv_current, ctlv_current, ctlid_current, proof_current = convert_to_ecpt(current_ballot_b64, GROUP)
    
    # Fetch last ballot and previous last ballot
    if cbr_length >= 2:
        last_ballot_b64, previous_last_ballot_b64 = await fetch_last_and_previouslast_ballot_from_bb(election_id, voter_id)
    else:
        # if there is no last previous ballot then we use the last ballot as the previous ballot
        last_ballot_b64, _ = await fetch_last_and_previouslast_ballot_from_bb(election_id, voter_id)
        previous_last_ballot_b64 = last_ballot_b64

    last_ballot = convert_to_ecpt(last_ballot_b64, GROUP)
    previous_last_ballot = convert_to_ecpt(previous_last_ballot_b64, GROUP)

    upk = EcPt.from_binary(base64.b64decode(pyballot.upk), GROUP) # Recreating voter public key as  EcPt object

    ctv = last_ballot[0]
    ctlv = last_ballot[1]
    ctlid = last_ballot[2]

    ct_i = (2 * ctlid[0], 2 * ctlid[1])
    c0, c1 = ctlv[0] - ctlid[0], ctlv[1] - ctlid[1]
    
    # last previous ballot from voter's CBR if it exists, otherwise the last ballot is also the last previous ballot
    ctv2 = previous_last_ballot[0]

    stmt_c = stmt((GENERATOR, pk_TS, pk_VS, upk, ctv_current, ctlv_current, ctlid_current, ct_i, c0, c1, ctv, ctv2), 
                (Secret(), Secret(), Secret(), Secret(), Secret(), Secret()), len(candidates))

    statement_verified = stmt_c.verify(proof_current)

    if not statement_verified: 
        print("verification failed")
        #NOTE: if failed to verify send message to voting app and display in UI "ballot not valid"
    else:
        print("\nVerification successful ballot")

    return stmt_c.verify(proof_current)

def convert_to_ecpt(ballot, GROUP):
    ct_v_b64, ct_lv_b64, ct_lid_b64, proof_b64 = ballot
    # Convert base64 encodings so all four elements are in binary
    ct_v_bin = [(base64.b64decode(x), base64.b64decode(y)) for (x, y) in ct_v_b64]
    ct_lv_bin = tuple(base64.b64decode(x) for x in ct_lv_b64)
    ct_lid_bin = tuple(base64.b64decode(x) for x in ct_lid_b64)
    proof_bin = base64.b64decode(proof_b64)
    
    # convert from binary into EcPt objects and a NIZK proof object.
    ct_v = [(EcPt.from_binary(x, GROUP), EcPt.from_binary(y, GROUP)) for (x, y) in ct_v_bin]
    ct_lv = (EcPt.from_binary(ct_lv_bin[0], GROUP), EcPt.from_binary(ct_lv_bin[1], GROUP))
    ct_lid = (EcPt.from_binary(ct_lid_bin[0], GROUP), EcPt.from_binary(ct_lid_bin[1], GROUP))
    if len(proof_b64) < 100: # suboptimal solution to avoid attempts at deserialising ballot0.
        proof = proof_bin
    else:
        proof = base.NIZK.deserialize(proof_bin)

    return (ct_v, ct_lv, ct_lid, proof)

# Function for re-encryption
# Parameters: generator, public key, ciphertext, randomness
def re_enc(g, pk, ct, r):
    c0, c1 = ct
    c0Prime = c0 + r*g
    c1Prime = c1 + r*pk

    return (c0Prime, c1Prime)

# Function for decryption
# Parameters: ciphertext & secret key.
def dec(ct, sk):
    c0, c1 = ct
    message = (c1 + (-sk*c0))

    return message

#NOTE: We recieve a ballot  with a uid, then we can get the cbr for that id, we are missing this
#NOTE we are missing the time aspect of potentially calling obfuscate many times asynchronously maybe??
    
async def obfuscate(voter_id, election_id):
    GROUP, GENERATOR, ORDER, cbr_length, candidates, pk_TS, pk_VS = await fetch_data(election_id, voter_id)
    voter_public_key_bin = await fetch_voter_public_key_from_bb(voter_id, election_id)
    upk = EcPt.from_binary(voter_public_key_bin, GROUP)

    # fetch VS secret key from json file keys.json
    sk_VS = fetch_vs_secret_key()

    # Fetch last ballot and previous last ballot
    if cbr_length >= 2:
        last_ballot_b64, previous_last_ballot_b64 = await fetch_last_and_previouslast_ballot_from_bb(election_id, voter_id)
    else:
        # if there is no last previous ballot then we use the last ballot as the previous ballot
        last_ballot_b64, _ = await fetch_last_and_previouslast_ballot_from_bb(election_id, voter_id)
        previous_last_ballot_b64 = last_ballot_b64

    last_ballot = convert_to_ecpt(last_ballot_b64, GROUP)
    previous_last_ballot = convert_to_ecpt(previous_last_ballot_b64, GROUP)

    #Generate a noise ballot
    r_v = Secret(value=ORDER.random())
    r_lv = Secret(value=ORDER.random())
    r_lid = Secret(value=ORDER.random())
    sk = Secret(value=sk_VS)

    ct_lv, ct_lid = last_ballot[1], last_ballot[2]

    ct_i=(2*ct_lid[0],2*ct_lid[1])  
    # ct_lv and ct_lid re-encrypted for the new obfuscated ballot.
    ct_lv_new=re_enc(GENERATOR, pk_VS, ct_i, r_lv.value) 
    ct_lid_new=re_enc(GENERATOR, pk_VS, ct_i, r_lid.value) 

    c0 = ct_lv[0]-ct_lid[0]
    c1 = ct_lv[1]-ct_lid[1]
    ct = (c0, c1)
    g_m_dec = dec(ct, sk.value)

    # If both ct_lv and ct_lid are encryptions of the same list, subtracting lid from lv will result in the equivalent of 0 (represented as 0*generator)
    if g_m_dec==0*GENERATOR:
    #if 1 = Dec(sk_vs, (ct_lv-1)-(ct_lid-1)) then we re-randomize the last ballot 
        ct_v=last_ballot[0]
        sim_relation=2
        print(f"[{cbr_length}] VS obfuscated last ballot")
    else : 
        ct_v=previous_last_ballot[0]
        sim_relation=1
        print(f"\033[31m[{cbr_length}] VS obfuscated previous last ballot\033[0m")
    
    ct_v_new = [re_enc(GENERATOR, pk_TS, ct_v[i], r_v.value) for i in range(len(candidates))]

    full_stmt=stmt((GENERATOR, pk_TS, pk_VS, upk, ct_v_new, ct_lv_new, ct_lid_new, ct_i, c0, c1, last_ballot[0], previous_last_ballot[0]),(r_v, Secret(), r_lv, r_lid, Secret(), sk), len(candidates))
    full_stmt.subproofs[0].set_simulated()
    
    #depending on whether 1 = Dec(sk_vs, (ct_lv-1)-(ct_lid-1)) or not we simulate R2 or R3, other than R1
    full_stmt.subproofs[sim_relation].set_simulated()
    nizk = full_stmt.prove({r_v: r_v.value, r_lv: r_lv.value, r_lid: r_lid.value, sk: sk.value})

    pyBallot: Ballot = construct_ballot(voter_id, upk, ct_v_new, ct_lv_new, ct_lid_new, nizk, election_id)
    print("pyballot created from obf")
    return pyBallot


def construct_ballot(voter_id, public_key, ct_v, ct_lv, ct_lid, proof, election_id):
    # Exporting bytes object for public key and encoding with base64
    public_key_b64 = base64.b64encode(public_key.export()).decode()

    # Encoding ciphertexts as base64.
    ct_v_b64 = [[base64.b64encode(x.export()).decode(), base64.b64encode(y.export()).decode()] for (x, y) in ct_v]
    ct_lv_b64 = [base64.b64encode(ct_lv[0].export()).decode(), base64.b64encode(ct_lv[1].export()).decode()]
    ct_lid_b64 = [base64.b64encode(ct_lid[0].export()).decode(), base64.b64encode(ct_lid[1].export()).decode()]
    
    # serialising and base64 encoding NIZK proof:
    proof_ser = base.NIZK.serialize(proof)
   # print(f"serialised proof: {proof_ser}")
    proof_b64 = base64.b64encode(proof_ser).decode()

    pyBallot = Ballot(
            voterid = voter_id,
            upk = public_key_b64,
            ctv = ct_v_b64,
            ctlv = ct_lv_b64,
            ctlid = ct_lid_b64,
            proof = proof_b64,
            electionid = election_id
        )
    return pyBallot

def fetch_vs_secret_key():    
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    SECRET_KEY_PATH = os.path.join(BASE_DIR, 'keys.json')

    with open(SECRET_KEY_PATH, 'r') as file:
        data = json.load(file)
    
    sk_VS = Bn.from_binary(base64.b64decode(data["secret_key"]))

    return sk_VS

async def fetch_data(election_id, voter_id):
    GROUP, GENERATOR, ORDER = await get_elgamal_params()
    cbr_length = await fetch_cbr_length_from_bb(voter_id, election_id)
    candidates: list = await fetch_candidates_from_bb(election_id)
    pk_TS, pk_VS = await fetch_public_keys_from_bb()

    return GROUP, GENERATOR, ORDER, cbr_length, candidates, pk_TS, pk_VS