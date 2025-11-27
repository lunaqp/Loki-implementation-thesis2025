from petlib.ec import EcGroup
import httpx
from modelsRA import ElGamalParams, VoterKey, VoterKeyList
import httpx
import base64
from coloursRA import BLUE, RED, CYAN
import duckdb

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
        save_keys_to_duckdb(voter_id, election_id, secret_key, public_key)

        voter_key = VoterKey(
            electionid = election_id,
            voterid = voter_id,
            publickey = base64.b64encode(public_key.export()).decode()
        )
        voter_key_list.voterkeylist.append(voter_key)
    return voter_key_list

def save_keys_to_duckdb(voter_id, election_id, secret_key, public_key):
    try:
        conn = duckdb.connect("/duckdb/voter-keys.duckdb")
        print(f"{CYAN}inserting keys in duckdb for voter {voter_id}")
        conn.execute(f"INSERT INTO VoterKeys VALUES (?, ?, ?, ?)", (voter_id, election_id, secret_key.binary(), public_key.export()))
    except Exception as e:
        print(f"{RED}error inserting keys in duckdb for voter {voter_id}: {e}")


async def send_keys_to_bb(voter_info: VoterKeyList):
    async with httpx.AsyncClient() as client:
        response = await client.post("http://bb_api:8000/receive-voter-keys", content = voter_info.model_dump_json())
        response.raise_for_status()
        print(f"{BLUE}voter public keys sent to BB")        

def fetch_keys_from_duckdb(voter_id, election_id):
    conn = duckdb.connect("/duckdb/voter-keys.duckdb")
    (secret_key, public_key) = conn.execute("""
            SELECT SecretKey, PublicKey
            FROM VoterKeys
            WHERE VoterID = ? AND ElectionID = ?
            """, (voter_id, election_id)).fetchone()

    return secret_key, public_key