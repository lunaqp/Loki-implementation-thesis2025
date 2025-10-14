from petlib.ec import EcGroup
import psycopg
import os
from cryptography.fernet import Fernet
import httpx
from fetchNewElection import CONNECTION_INFO

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

# Generate private and public keys for each voter
def keygen(voter_list, election_id):
    voter_info = []
    for id in voter_list:
        secret_key = ORDER.random() 
        public_key = secret_key * GENERATOR
        enc_secret_key = encrypt_key(secret_key)
        voter_info.append([election_id, id, public_key, enc_secret_key])

    return voter_info

# Save keymaterial to database for each voter
def save_keys_to_db(voter_info):
    conn = psycopg.connect(CONNECTION_INFO)
    cur = conn.cursor()
    for (election_id, voter_id, public_key, enc_secret_key) in voter_info:
        cur.execute("""
                    INSERT INTO VoterParticipatesInElection (ElectionID, VoterID, PublicKey, SecretKey)
                    VALUES (%s, %s, %s, %s)
                    """, (election_id, voter_id, public_key.export(), enc_secret_key))
    conn.commit()
    cur.close()
    conn.close()

def encrypt_key(secret_key):
    ENCRYPTION_KEY = os.getenv("VOTER_SK_ENCRYPTION_KEY") # Symmetric key - saved in docker-compose.yml. NOTE: Should be moved outside of repository.
    cipher = Fernet(ENCRYPTION_KEY)
    # the encrypt() function returns a URL-safe base64-encoded secure message that cannot be read or altered without the key - a “Fernet token”.
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
