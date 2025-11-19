import duckdb
import base64
from coloursVA import CYAN, RED

def save_keys_to_duckdb(voter_id, election_id, enc_secret_key, public_key):
    try:
        conn = duckdb.connect("/duckdb/voter-keys.duckdb")
        print(f"{CYAN}inserting keys in duckdb for voter {voter_id}")
        conn.execute(f"INSERT INTO VoterKeys VALUES (?, ?, ?, ?)", (voter_id, election_id, base64.b64decode(enc_secret_key), base64.b64decode(public_key)))
        conn.table("VoterKeys").show()
    except Exception as e:
        print(f"{RED}error inserting keys in duckdb for voter {voter_id}: {e}")

def save_voter_login(voter_id):
    username = f"voter{voter_id}"
    password = f"pass{voter_id}"
    try:
        conn = duckdb.connect("/duckdb/voter-keys.duckdb")
        print(f"{CYAN}inserting login info in duckdb for voter {voter_id}")
        conn.execute(f"INSERT INTO VoterLogin (Username, Password) VALUES (?, ?) ON CONFLICT(Username) DO NOTHING", (username, password))
        conn.table("VoterLogin").show() 
    except Exception as e:
        print(f"{RED}error inserting login info in duckdb for voter {voter_id}: {e}")