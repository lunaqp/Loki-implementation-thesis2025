from petlib.ec import EcGroup
import os
from cryptography.fernet import Fernet
import httpx
from modelsRA import ElGamalParams, VoterKey, VoterKeyList
import httpx
import base64
from fastapi import HTTPException

def generate_group_order():
    # Using the petlib library group operations to generate group and group values
    GROUP = EcGroup()
    GENERATOR = GROUP.generator()
    ORDER = GROUP.order()
    return GROUP, GENERATOR, ORDER

GROUP, GENERATOR, ORDER = generate_group_order()
print(f"generator: {GENERATOR}")
print(f"order: {ORDER}")
print(f"group: {GROUP}")

async def send_params_to_bb():
    print("sending elgamal params to BB...")
    
    params = ElGamalParams(
        group = GROUP.nid(),
        generator = base64.b64encode(GENERATOR.export()).decode(),
        order = base64.b64encode(ORDER.binary()).decode()
    )

    async with httpx.AsyncClient() as client:
        response = await client.post("http://bb_api:8000/receive-params", json=params.model_dump())

    try:
        response_data = response.json() if response.content else None
    except ValueError:
        response_data = response.text

    return {"status": "sent elgamal Parameters to BB", "response": response_data}

# Generate private and public keys for each voter
async def keygen(voter_list, election_id):
    voter_key_list = VoterKeyList(voterkeylist=[])

    for id in voter_list:
        secret_key = ORDER.random() # save secret key locally.
        print(f"secret key type: {type(secret_key)}")
        public_key = secret_key * GENERATOR
        print(f"public key type: {type(public_key)}")
        #enc_secret_key = encrypt_key(secret_key) # TODO: Either reintroduce encryption or remove from code
        print(f"secret key: {secret_key}")
        await send_keys_to_va(id, election_id, secret_key, public_key)

        voter_key = VoterKey(
            electionid = election_id,
            voterid = id,
            publickey = base64.b64encode(public_key.export()).decode()
        )
        voter_key_list.voterkeylist.append(voter_key)
    
    return voter_key_list

async def send_keys_to_bb(voter_info: VoterKeyList):
    async with httpx.AsyncClient() as client:
        response = await client.post("http://bb_api:8000/receive-voter-keys", content = voter_info.model_dump_json())
        response.raise_for_status()
        print("voter public keys sent to BB")        

async def send_keys_to_va(voter_id, election_id, secret_key, public_key):
    data = {"voter_id": voter_id, "election_id": election_id, "secret_key": base64.b64encode(secret_key.binary()).decode(), "public_key":base64.b64encode(public_key.export()).decode() } # decode() converts b64 bytes to string

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post("http://va_api:8000/receive-keys", json=data)
            response.raise_for_status() # gets http status code
          
            return response.json()
    except Exception as e:
        print(f"Error sending keys to VA: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to send secret key to VA: {str(e)}")     


def encrypt_key(secret_key):
    ENCRYPTION_KEY = os.getenv("VOTER_SK_ENCRYPTION_KEY") # Symmetric key - saved in docker-compose.yml. NOTE: Should be moved outside of repository.
    cipher = Fernet(ENCRYPTION_KEY)
    # the encrypt() function returns a URL-safe base64-encoded secure message that cannot be read or altered without the key - a “Fernet token”.
    encrypted_secret_key = cipher.encrypt(str(secret_key).encode()) # Fernet needs byte objects or strings.
    print(f"Type of encrypted key: {type(encrypted_secret_key)}")
    return encrypted_secret_key

# Only for testing if decryption worked - might be relevant in VotingApp
# def decrypt_key():
#     conn = psycopg.connect(dbname=DBNAME, user=DBUSER, password=DBPASSWORD, host=DBHOST, port=DBPORT)
#     cur = conn.cursor()
#     cur.execute("""
#                 SELECT SecretKey
#                 FROM VoterParticipatesInElection
#                 WHERE VoterID = 0 AND ElectionID = 0
#                 """)
#     (record,) = cur.fetchone()
#     conn.commit()
#     cur.close()
#     conn.close()
#     ENCRYPTION_KEY = os.getenv("VOTERKEYMATERIAL_KEY") # Symmetric key - saved in docker-compose.yml
#     cipher = Fernet(ENCRYPTION_KEY)
#     decrypted_secret_key = cipher.decrypt(record)
#     print(decrypted_secret_key)
