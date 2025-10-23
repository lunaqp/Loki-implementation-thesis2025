from zksk import Secret
from statement import stmt
import httpx
from fastapi import HTTPException
import base64
from petlib.ec import EcPt, EcGroup, Bn
from modelsVA import ElGamalParams, Ballot
import os
import psycopg
import duckdb
from cryptography.fernet import Fernet
import httpx


DB_NAME = os.getenv("POSTGRES_DB", "appdb")
DB_USER = os.getenv("POSTGRES_USER", "postgres")
DB_PASS = os.getenv("POSTGRES_PASSWORD", "postgres")
DB_HOST = os.getenv("POSTGRES_HOST", "db")  # docker service name
DB_PORT = int(os.getenv("POSTGRES_PORT", "5432"))
CONNECTION_INFO = f"dbname={DB_NAME} user={DB_USER} password={DB_PASS} host={DB_HOST} port={DB_PORT}"

conn = psycopg.connect(CONNECTION_INFO)

cur = conn.cursor()

async def get_elgamal_params():
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
            
            print(f"elgamal params fetched from BB: {GROUP}, \n {GENERATOR} \n {ORDER}")
            return GROUP, GENERATOR, ORDER
        
        except Exception as e:
            raise HTTPException(status_code=502, detail=f"Unable to fetch elgamal params: {e}") #NOTE: What would be the most correct status_codes for different scenarios?


async def fetch_candidates_from_bb(election_id):
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"http://bb_api:8000/candidates?election_id={election_id}")
            response.raise_for_status() 
          
            data = response.json()
            candidates_list: list = []
            for candidate_id in data["id"]:
                candidates_list.append(candidate_id)

            return candidates_list
    except Exception as e:
        print(f"Error fetching candidates from BB {e}")
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

def fetch_last_and_previouslast_ballot(voter_id, election_id):
    cur.execute("""
                SELECT CtCandidate, CtVoterList, CtVotingServerList, Valid
                FROM VoterParticipatesInElection p
                JOIN VoterCastsBallot c 
                ON p.ElectionID = c.ElectionID AND p.VoterID = c.VoterID
                JOIN Ballots b
                ON b.ID = c.BallotID
                WHERE p.ElectionID = %s AND p.VoterID = %s
                ORDER BY c.VoteTimestamp DESC
                LIMIT 2;
                """, (election_id, voter_id))
    (last_ballot, previous_last_ballot) = cur.fetchall()
    return last_ballot, previous_last_ballot


def fetch_cbr_length(voter_id, election_id):
    cur.execute("""
                SELECT COUNT(*)
                FROM VoterParticipatesInElection p
                JOIN VoterCastsBallot c 
                ON p.ElectionID = c.ElectionID AND p.VoterID = c.VoterID
                WHERE p.ElectionID = %s AND p.VoterID = %s
                """, (election_id, voter_id))
    (cbr_length,) = cur.fetchone()  # fetchone returns a tuple like (count,)
    return cbr_length

def bin_to_int(lst, size):
   b=[0]*size
   #the new bit is set to 1
   b[-1]=1
   for i in lst:
      b[i]=1  
   return int(''.join(str(bit) for bit in b),2)

def fetch_keys(voter_id, election_id):
    conn = duckdb.connect("/duckdb/voter-keys.duckdb")
    print(f"fetching keys for {voter_id}")
    (enc_secret_key, public_key) = conn.execute("""
            SELECT SecretKey, PublicKey
            FROM VoterSecretKeys
            WHERE VoterID = ? AND ElectionID = ?
            """, (voter_id, election_id)).fetchone()
    usk_bin = decrypt_key(enc_secret_key)
    
    return usk_bin, public_key

def decrypt_key(enc_secret_key):
    ENCRYPTION_KEY = os.getenv("VOTER_SK_DECRYPTION_KEY") # Symmetric key - saved in docker-compose.yml
    cipher = Fernet(ENCRYPTION_KEY)
    decrypted_secret_key = cipher.decrypt(enc_secret_key)

    return decrypted_secret_key

def vote(usk, v, lv_list, election_id, voter_id):
    GROUP, GENERATOR, ORDER = get_elgamal_params()
    pk_TS, pk_VS = fetch_public_keys_from_bb()
    last_ballot, previous_last_ballot = fetch_last_and_previouslast_ballot(election_id, voter_id)
    cbr_length = fetch_cbr_length(voter_id, election_id)
    candidates = fetch_candidates_from_bb(election_id)
    usk_bin, public_key = fetch_keys(voter_id, election_id)
    usk = EcPt.from_binary(usk_bin, GROUP)

    secret_usk = Secret(value=usk)
    R1_r_v = Secret(value=ORDER.random())
    R1_r_lv = Secret(value=ORDER.random())
    R1_r_lid = Secret(value=ORDER.random())
    R1_v = [0]*candidates
    
    for i in range(candidates):
        R1_v[i] = Secret(value=0)
    if v>0:
        #generate R1_v based on the vote otherwise abstention
        R1_v[v-1] = Secret(value=1)

    #generate lv based on the indexes in lv_list
    R1_lv = Secret(value=bin_to_int(lv_list, cbr_length+1))

    #last ballot from voter's CBR
    ct_v, ct_lv, ct_lid, proof = last_ballot

    #generating the new ballot
    ct_i = (2*ct_lid[0],2*ct_lid[1]) 
    ct_v = [enc(GENERATOR, pk_TS, R1_v[i].value, R1_r_v.value) for i in range(candidates)]
    ct_lv = enc(GENERATOR, pk_VS, R1_lv.value, R1_r_lv.value) 
    ct_lid = re_enc(GENERATOR, pk_VS, (ct_i[0], GENERATOR+ct_i[1]), R1_r_lid.value)
    c0 = ct_lv[0]-ct_lid[0]
    c1 = ct_lv[1]-ct_lid[1]

    if v>0:
        print(f"[{cbr_length}] Voted for candidate {v} with voter list {lv_list}") 
    else: print(f"[{cbr_length}] Voted for no candidate (abstention) with voter list {lv_list}")

    full_stmt=stmt((GENERATOR, pk_TS, pk_VS, usk*GENERATOR, ct_v, ct_lv, ct_lid, ct_i, c0, c1, ct_v, previous_last_ballot), (R1_r_v, R1_lv, R1_r_lv, R1_r_lid, secret_usk, Secret()), candidates)
    simulation_indexes=[]

    #if the vote is for abstention then we need to simulate the proof for all candidates
    simulation_indexes=[i for i in range(candidates)] if v==0 else [i for i in range(candidates+1) if i!=v-1]

    #setting the relations to be simulated
    for i in simulation_indexes:
        full_stmt.subproofs[0].subproofs[0].subproofs[i].set_simulated()
    full_stmt.subproofs[1].set_simulated()
    full_stmt.subproofs[2].set_simulated()
    
    #constructing the witness for each candidate vote encryption 
    R1_v_str=[('R1_v'+str([i]), R1_v[i].value) for i in range(candidates)]
    sec_dict=dict(R1_v_str)

    #prove the statement
    nizk = full_stmt.prove(sec_dict.update({R1_r_v: R1_r_v.value, R1_lv: R1_lv.value, R1_r_lv: R1_r_lv.value, R1_r_lid: R1_r_lid.value, secret_usk: secret_usk.value}))
    
    pyBallot = constructBallot(voter_id, public_key, ct_v, ct_lv, ct_lid, nizk)
    return pyBallot

def constructBallot(voter_id, public_key, ct_v, ct_lv, ct_lid, proof):
    pyBallot = Ballot(
            voterid = voter_id,
            upk = public_key,
            ctv = ct_v,
            ctlv = ct_lv,
            ctlid = ct_lid,
            proof = proof
        )
    return pyBallot

async def send_ballot_to_VS(pyBallot:Ballot):
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post("http://vs_api:8000/receive-ballot", json=pyBallot.model_dump()) 
            response.raise_for_status()
    except Exception as e:
        print("Error sending ballot", {e})
    

def enc(g, pk, m, r):
    c0 = r*g
    c1 = m*g + r*pk

    return (c0, c1)


def dec(ct, sk):
    c0, c1 = ct
    message = (c1 + (-sk*c0))

    return message


def re_enc(g, pk, ct, r):
    c0, c1 = ct
    c0Prime = c0 + r*g
    c1Prime = c1 + r*pk

    return (c0Prime, c1Prime)