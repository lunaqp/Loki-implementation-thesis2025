from petlib.ec import EcGroup
import psycopg
import os
from cryptography.fernet import Fernet
import httpx

DATABASE_URL = os.getenv("DATABASE_URL")

DBNAME = os.getenv("POSTGRES_DB", "appdb")
DBUSER = os.getenv("POSTGRES_USER", "postgres")
DBPASSWORD = os.getenv("POSTGRES_PASSWORD", "postgres")
DBHOST = os.getenv("POSTGRES_HOST", "db")
DBPORT = os.getenv("POSTGRES_PORT", "5432")

def generate_group_order():
    # Using the petlib library group operations to generate group and group values
    group = EcGroup()
    g = group.generator()
    order = group.order()
    return g, order

g, order = generate_group_order()

def save_globalinfo_to_db():
    print(f"g: {g}")
    print(f"order: {order}")
    conn = psycopg.connect(dbname=DBNAME, user=DBUSER, password=DBPASSWORD, host=DBHOST, port=DBPORT)
    cur = conn.cursor()
    cur.execute("""
                UPDATE GlobalInfo
                SET Generator = %s, OrderP = %s
                WHERE ID = 0
                """, (str(g), int(order)))
    conn.commit()
    cur.close()
    conn.close()

# Notify TallyingServer and VotingServer of g and order being saved to database.
async def notify_ts_and_vs():
    async with httpx.AsyncClient() as client:
        # Call TallyingServer:
        resp_TS = await client.get("http://ts_api:8000/ts_resp")
        # Call VotingServer:
        resp_VS = await client.get("http://vs_api:8000/vs_resp")
    return resp_TS.json(), resp_VS.json()


voter_list = {
  "voters": [
    { "id": 0, "name": "Emma" },
    { "id": 1, "name": "Thomas" },
    { "id": 2, "name": "James" },
    { "id": 3, "name": "Karen" }
  ]
}

#Alternative:
def keygen(voter_list, election_id):
    voter_info = []
    for id in voter_list:
        secret_key = order.random() 
        print(f"secret key type: {type(secret_key)}") # type = petlib.bn.Bn
        public_key = secret_key * g
        print(f"pk: {public_key}")
        print(f"sk: {secret_key}")
        enc_secret_key = encrypt_key(secret_key)
        print(f"encrypted sk: {enc_secret_key}")
        voter_info.append([election_id, id, public_key, enc_secret_key])
    return voter_info

# Alternative
def save_keys_to_db(voter_info):
    conn = psycopg.connect(dbname=DBNAME, user=DBUSER, password=DBPASSWORD, host=DBHOST, port=DBPORT)
    cur = conn.cursor()
    for (election_id, voter_id, public_key, enc_secret_key) in voter_info:
        cur.execute("""
                    INSERT INTO VoterParticipatesInElection (ElectionID, VoterID, PublicKey, SecretKey)
                    VALUES (%s, %s, %s, %s)
                    """, (election_id, voter_id, str(public_key), enc_secret_key))
    conn.commit()
    cur.close()
    conn.close()

def encrypt_key(secret_key):
    ENCRYPTION_KEY = os.getenv("VOTER_SK_ENCRYPTION_KEY") # Symmetric key - saved in docker-compose.yml
    cipher = Fernet(ENCRYPTION_KEY)
    # encrypt() returns: A URL-safe base64-encoded secure message that cannot be read or altered without the key. This is referred to as a “Fernet token”.
    encrypted_secret_key = cipher.encrypt(str(secret_key).encode()) # Fernet needs byte objects or strings.
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
