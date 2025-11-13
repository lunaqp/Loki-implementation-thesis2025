from petlib.ec import EcGroup
import os
import httpx
from modelsRA import ElGamalParams, VoterKey, VoterKeyList
import httpx
import base64
from fastapi import HTTPException
from coloursRA import BLUE, RED
from petlib.cipher import Cipher
import docker
import asyncio

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

    for voter_id in voter_list:
        secret_key = ORDER.random()
        public_key = secret_key * GENERATOR
        enc_secret_key, iv = encrypt_key(secret_key)
        
        container_name = create_va_instance(voter_id)
        await send_keys_to_va(voter_id, election_id, enc_secret_key, public_key, iv, container_name)

        voter_key = VoterKey(
            electionid = election_id,
            voterid = voter_id,
            publickey = base64.b64encode(public_key.export()).decode()
        )
        voter_key_list.voterkeylist.append(voter_key)
    
    return voter_key_list

async def send_keys_to_bb(voter_info: VoterKeyList):
    async with httpx.AsyncClient() as client:
        response = await client.post("http://bb_api:8000/receive-voter-keys", content = voter_info.model_dump_json())
        response.raise_for_status()
        print(f"{BLUE}voter public keys sent to BB")        

async def send_keys_to_va(voter_id, election_id, secret_key, public_key, iv, container_name):
    data = {"voter_id": voter_id, "election_id": election_id, "secret_key": base64.b64encode(secret_key).decode(), "iv": base64.b64encode(iv).decode(), "public_key":base64.b64encode(public_key.export()).decode() } # decode() converts b64 bytes to string
    url = f"http://{container_name}:8000/receive-keys"
    await wait_for_va(container_name)
    print("sending key to", container_name)
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=data)
            response.raise_for_status() # gets http status code

            print("key sent to", container_name)
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


def create_va_instance(voter_id):
    client = docker.from_env()
    container_name = f"va_api_{voter_id}"
    existing = client.containers.list(filters={"name": container_name})
    if existing:
        return container_name

    image_name = "loki-implementation-thesis2025-va_api:latest"
    network_name = "loki-implementation-thesis2025_default"
    volume_name = f"va_data_{voter_id}"
    try:
        client.volumes.get(volume_name)
    except docker.errors.NotFound:
        client.volumes.create(name=volume_name)

    client.containers.run(
        image=image_name,
        name=container_name,
        detach=True,
        network=network_name,
        environment={
            "BB_API_URL": "http://bb_api:8000",
            "VOTER_SK_DECRYPTION_KEY": "Al43dQKlM/aAjb5zBNYXBQ==",
            "DUCKDB_PATH": "/duckdb/voter-keys.duckdb",
            "VOTER_ID": str(voter_id),
        },
        volumes={volume_name: {"bind": "/duckdb", "mode": "rw"}},
    )
    return container_name

async def wait_for_va(container_name, timeout=30):
    url = f"http://{container_name}:8000/health" 
    start_time = asyncio.get_event_loop().time()
    
    while True:
        try:
            async with httpx.AsyncClient() as client:
                r = await client.get(url, timeout=2)
                if r.status_code == 200:
                    print(f"{container_name} is ready")
                    return
        except (httpx.ConnectError, httpx.ReadTimeout):
            pass #TODO: figure out if pass makes sense to use here.

        if asyncio.get_event_loop().time() - start_time > timeout:
            raise TimeoutError(f"{container_name} did not become ready in {timeout} seconds")
        
        await asyncio.sleep(1) 


def create_va_web_instance(voter_id):
    client = docker.from_env()
    container_name = f"va_web_{voter_id}"
    existing = client.containers.list(filters={"name": container_name})
    if existing:
        return container_name

    image_name = "loki-implementation-thesis2025-va_web:latest"
    network_name = "loki-implementation-thesis2025_default"
    
    client.containers.run(
        image=image_name,
        name=container_name,
        detach=True,
        network=network_name,
        environment={
            "VITE_API_VOTINGAPP": f"http://va_api_{voter_id}:8000",
            "VOTER_ID": str(voter_id),
        },
    )
    return container_name
