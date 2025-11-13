from petlib.ec import EcGroup
import os
import httpx
from modelsRA import ElGamalParams, VoterKey, VoterKeyList
import httpx
import base64
from fastapi import HTTPException
from coloursRA import BLUE, RED
from petlib.cipher import Cipher

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
    print(f"{BLUE}sending elgamal params to BB...")
    
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
        secret_key = ORDER.random()
        public_key = secret_key * GENERATOR
        enc_secret_key, iv = encrypt_key(secret_key)
        
        await send_keys_to_va(id, election_id, enc_secret_key, public_key, iv)

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
        print(f"{BLUE}voter public keys sent to BB")        

async def send_keys_to_va(voter_id, election_id, secret_key, public_key, iv):
    data = {"voter_id": voter_id, "election_id": election_id, "secret_key": base64.b64encode(secret_key).decode(), "iv": base64.b64encode(iv).decode(), "public_key":base64.b64encode(public_key.export()).decode() } # decode() converts b64 bytes to string

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post("http://va_api:8000/receive-keys", json=data)
            response.raise_for_status() # gets http status code
          
            return response.json()
    except Exception as e:
        print(f"{RED}Error sending keys to VA: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to send secret key to VA: {str(e)}")     

def encrypt_key(secret_key):
    secret_key_bin = secret_key.binary()
    aes_cipher = Cipher("AES-128-CTR")
    iv = os.urandom(16)
    ENC_KEY = base64.b64decode(os.getenv("VOTER_SK_ENCRYPTION_KEY")) # Symmetric key - saved in docker-compose.yml
    enc = aes_cipher.enc(ENC_KEY, iv)
    enc_secret_key = enc.update(secret_key_bin)
    enc_secret_key += enc.finalize()

    return (enc_secret_key, iv)