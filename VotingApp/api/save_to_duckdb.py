"""DuckDB persistence for the Voting App.

This module persists:
- All voters secret/public key material for a given election into DuckDB.
- Simple demo login credentials for voters into DuckDB.

Key material is expected to be base64-encoded strings when provided to ``save_keys_to_duckdb`` and is decoded to raw bytes before storage.
"""

import duckdb
import base64
from coloursVA import CYAN, RED

def save_keys_to_duckdb(voter_id, election_id, enc_secret_key, public_key):
    """Save a voter's key material into DuckDB.

    Args:
        voter_id: Voter identifier.
        election_id: Election identifier.
        enc_secret_key: Base64-encoded secret key.
        public_key: Base64-encoded public key.

    The function decodes base64 inputs and stores them as BLOB fields.
    """
    try:
        conn = duckdb.connect("/duckdb/voter-keys.duckdb")
        print(f"{CYAN}inserting keys in duckdb for voter {voter_id}")
        conn.execute(f"INSERT INTO VoterKeys VALUES (?, ?, ?, ?)", (voter_id, election_id, base64.b64decode(enc_secret_key), base64.b64decode(public_key)))
        conn.table("VoterKeys").show()
    except Exception as e:
        print(f"{RED}error inserting keys in duckdb for voter {voter_id}: {e}")

def save_voter_login(voter_id):
    """Insert a voter's login credentials into DuckDB.

    Credentials are derived from voter_id:
    - username: ``voter{voter_id}``
    - password: ``pass{voter_id}``

    Args:
        voter_id: Voter identifier.

    Intended for usability testing purposes only.
    """
    username = f"voter{voter_id}"
    password = f"pass{voter_id}"
    try:
        conn = duckdb.connect("/duckdb/voter-keys.duckdb")
        print(f"{CYAN}inserting login info in duckdb for voter {voter_id}")
        conn.execute(f"INSERT INTO VoterLogin (Username, Password) VALUES (?, ?) ON CONFLICT(Username) DO NOTHING", (username, password))
        conn.table("VoterLogin").show() 
    except Exception as e:
        print(f"{RED}error inserting login info in duckdb for voter {voter_id}: {e}")