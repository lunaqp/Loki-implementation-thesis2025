import psycopg
import os
from modelsBB import NewElectionData, VoterKeyList, Ballot
import base64
import hashlib
from hashBB import hash_ballot
import json


DB_NAME = os.getenv("POSTGRES_DB", "appdb")
DB_USER = os.getenv("POSTGRES_USER", "postgres")
DB_PASS = os.getenv("POSTGRES_PASSWORD", "postgres")
DB_HOST = os.getenv("POSTGRES_HOST", "db")  # docker service name
DB_PORT = int(os.getenv("POSTGRES_PORT", "5432"))
CONNECTION_INFO = f"dbname={DB_NAME} user={DB_USER} password={DB_PASS} host={DB_HOST} port={DB_PORT}" # all info that psycopg needs to connect to db


## ---------------- WRITING TO DB ---------------- ##


# loading a newly received election into the database:
#SQL statements to be executed
SQL_INSERT_ELECTION = """
INSERT INTO Elections (ID, Name, ElectionStart, ElectionEnd)
VALUES (%s, %s, %s, %s)
ON CONFLICT (ID) DO NOTHING;
"""

SQL_INSERT_BALLOT = """
INSERT INTO Ballots (CtCandidate, CtVoterList, CtVotingServerList, Proof, BallotHash)
VALUES (%s, %s, %s, %s, %s)
ON CONFLICT (ID) DO NOTHING
RETURNING ID;
"""

SQL_INSERT_RELATION_VOTERCASTBALLOT = """
INSERT INTO VoterCastsBallot (BallotID, VoterID, ElectionID, VoteTimestamp)
VALUES (%s, %s, %s, %s)
ON CONFLICT (BallotID) DO NOTHING;
"""

SQL_INSERT_CANDIDATE = """
INSERT INTO Candidates (ID, Name)
VALUES (%s, %s)
ON CONFLICT (ID) DO NOTHING;
"""

SQL_LINK_CANDIDATE_RUNS = """
INSERT INTO CandidateRunsInElection (CandidateID, ElectionID)
VALUES (%s, %s)
ON CONFLICT (CandidateID, ElectionID) DO NOTHING;
"""

SQL_INSERT_VOTER = """
INSERT INTO Voters (ID, Name)
VALUES (%s, %s)
ON CONFLICT (ID) DO NOTHING;
"""

SQL_INSERT_IMAGES = """
INSERT INTO Images (ImageFilename, BallotID)
VALUES (%s, %s)
ON CONFLICT (BallotID) DO NOTHING;
"""

def load_election_into_db(payload: NewElectionData):

    #Writes the election, candidates, voters and relations to the DB.
    eid = payload.election.id

    with psycopg.connect(CONNECTION_INFO) as conn:
        with conn.cursor() as cur:
            # Insert NewElection
            cur.execute(
                SQL_INSERT_ELECTION,
                (eid, payload.election.name, payload.election.start, payload.election.end),
            )
            # Insert Candidates + relation
            for c in payload.candidates:
                cur.execute(SQL_INSERT_CANDIDATE, (c.id, c.name))
                cur.execute(SQL_LINK_CANDIDATE_RUNS, (c.id, eid))
            # Insert Voters + relation (no keys yet)
            for v in payload.voters:
                cur.execute(SQL_INSERT_VOTER, (v.id, v.name))


def load_ballot_into_db(pyBallot: Ballot):
    # recomputed = hash_ballot(pyBallot)
    # if pyBallot.hash and pyBallot.hash != recomputed:
    #     raise ValueError("Ballot hash mismatch")

    # hashed_ballot = recomputed
    # print("BB hash:", recomputed)

    election_id = pyBallot.electionid
    ctv = json.dumps(pyBallot.ctv) # json string of base64 encoding
    ctlv = json.dumps(pyBallot.ctlv)
    ctlid = json.dumps(pyBallot.ctlid)
    proof = base64.b64decode(pyBallot.proof)
    
    hashed_ballot = hash_ballot(pyBallot) 
    timestamp = pyBallot.timestamp

    with psycopg.connect(CONNECTION_INFO) as conn:
        with conn.cursor() as cur:
            
            cur.execute(
                SQL_INSERT_BALLOT,
                (ctv, ctlv, ctlid, proof, hashed_ballot),
            )
            ballot_id = cur.fetchone()[0]

            cur.execute(
                SQL_INSERT_RELATION_VOTERCASTBALLOT,
                (ballot_id, pyBallot.voterid, election_id, timestamp)
            )
            cur.execute(
                SQL_INSERT_IMAGES,
                (pyBallot.imagepath, ballot_id)
            )

# saving group, generator and order to database after receiving them from RA.
def save_elgamalparams(GROUP, GENERATOR, ORDER):
    print("saving Elgamal parameters to database")
    conn = psycopg.connect(CONNECTION_INFO)
    cur = conn.cursor()
    cur.execute("""
                UPDATE GlobalInfo
                SET GroupCurve = %s, Generator = %s, OrderP = %s
                WHERE ID = 0
                """, (GROUP, GENERATOR, ORDER))
    conn.commit()
    cur.close()
    conn.close()

def save_key_to_db(service, KEY):
    if service == "TS":
        column = "PublicKeyTallyingServer"
    elif service == "VS":
        column = "PublicKeyVotingServer"
        
    conn = psycopg.connect(CONNECTION_INFO)
    cur = conn.cursor()
    cur.execute(f"""
        UPDATE GlobalInfo
        SET {column} = %s
        WHERE ID = 0
        """, (KEY,))
    conn.commit()
    cur.close()
    conn.close()
    print(f"public key received from {service} and saved to database")

# Save keymaterial to database for each voter
def save_voter_keys_to_db(voter_key_list: VoterKeyList):
    conn = psycopg.connect(CONNECTION_INFO)
    cur = conn.cursor()
    print("saving voter public keys to database")
    list = voter_key_list.voterkeylist
    for voter_key in list:
        cur.execute("""
                    INSERT INTO VoterParticipatesInElection (ElectionID, VoterID, PublicKey)
                    VALUES (%s, %s, %s)
                    """, (voter_key.electionid, voter_key.voterid, base64.b64decode(voter_key.publickey))) # Decode base64 to retrieve byte object
    conn.commit()
    cur.close()
    conn.close()


## ---------------- READING FROM DB ---------------- ##


async def fetch_params():
    with psycopg.connect(CONNECTION_INFO) as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT GroupCurve, Generator, OrderP
                FROM GlobalInfo
                WHERE ID = 0
            """)
            (GROUP, GENERATOR, ORDER) = cur.fetchone()
            return GROUP, GENERATOR, ORDER
        cur.close()
        conn.close()

# Query for fetching all voters participating in a given election
def fetch_voters_for_election(election_id):
    conn = psycopg.connect(CONNECTION_INFO)
    cur = conn.cursor()
    cur.execute("""
                SELECT v.ID, v.Name
                FROM Voters v
                Join VoterParticipatesInElection ve on v.ID = ve.VoterID
                WHERE ve.ElectionID = %s;"""
                ,(election_id,))
    records = cur.fetchall()
    return records

# Query for fetching all candidates running in a given election id:
def fetch_candidates_for_election(election_id): # Should cursor be given as parameter?
    conn = psycopg.connect(CONNECTION_INFO)
    cur = conn.cursor()
    cur.execute("""
                SELECT c.ID, c.Name
                FROM Candidates c
                JOIN CandidateRunsInElection cr on c.ID = cr.CandidateID
                WHERE cr.ElectionID = %s;""",
                (election_id,)
                )
    # Retrieve query results
    records = cur.fetchall()
    return records

# Fetch startdate from database
def fetch_election_dates(election_id):
    conn = psycopg.connect(CONNECTION_INFO)
    cur = conn.cursor()
    cur.execute("""
                SELECT ElectionStart, ElectionEnd
                FROM Elections
                WHERE ID = %s
                """, (election_id,))
    election_startdate, election_enddate = cur.fetchone()
    return election_startdate, election_enddate

# Fetch public keys for Tallying Server and Voting Server
def fetch_public_keys_tsvs():
    conn = psycopg.connect(CONNECTION_INFO)
    cur = conn.cursor()
    cur.execute("""
                SELECT PublicKeyTallyingServer, PublicKeyVotingServer
                FROM GlobalInfo
                WHERE ID = 0
                """)
    public_key_ts_bin, public_key_vs_bin = cur.fetchone()
    cur.close()
    conn.close()

    return public_key_ts_bin, public_key_vs_bin

# Fetch public key for a given voter in a given election
def fetch_voter_public_key(voter_id, election_id):
    conn = psycopg.connect(CONNECTION_INFO)
    cur = conn.cursor()
    cur.execute("""
                SELECT PublicKey
                FROM VoterParticipatesInElection
                WHERE VoterID = %s AND ElectionID = %s;
                """, (voter_id, election_id))
    (upk,) = cur.fetchone()
    
    cur.close()
    conn.close()

    return upk

def fetch_last_and_previouslast_ballot(voter_id, election_id):
    conn = psycopg.connect(CONNECTION_INFO)
    cur = conn.cursor()
    cur.execute("""
                SELECT CtCandidate, CtVoterList, CtVotingServerList, Proof
                FROM VoterParticipatesInElection p
                JOIN VoterCastsBallot c 
                ON p.ElectionID = c.ElectionID AND p.VoterID = c.VoterID
                JOIN Ballots b
                ON b.ID = c.BallotID
                WHERE p.ElectionID = %s AND p.VoterID = %s
                ORDER BY c.VoteTimestamp DESC
                LIMIT 2;
                """, (election_id, voter_id))
    rows = cur.fetchall()

    # In case only one row is in the database (ballot0):
    if len(rows) == 1:
        last_ballot_b64 = serialise_ballot_cts(rows[0])
        return last_ballot_b64, None

    last_ballot_b64 = serialise_ballot_cts(rows[0])
    previous_last_ballot_b64 = serialise_ballot_cts(rows[1])

    return last_ballot_b64, previous_last_ballot_b64

# Helper function for sending ct_bar values.
def serialise_ballot_cts(ballot_ct):
    ct_v_b64 = ballot_ct[0]
    ct_lv_b64 = ballot_ct[1]
    ct_lid_b64 = ballot_ct[2]
    
    # serialising and base64 encoding NIZK proof:
    proof_b64 = base64.b64encode(ballot_ct[3]).decode()
    return (ct_v_b64, ct_lv_b64, ct_lid_b64, proof_b64)

def fetch_cbr_length(voter_id, election_id):
    conn = psycopg.connect(CONNECTION_INFO)
    cur = conn.cursor()
    cur.execute("""
                SELECT COUNT(*)
                FROM VoterParticipatesInElection p
                JOIN VoterCastsBallot c 
                ON p.ElectionID = c.ElectionID AND p.VoterID = c.VoterID
                WHERE p.ElectionID = %s AND p.VoterID = %s
                """, (election_id, voter_id))
    (cbr_length,) = cur.fetchone()  # fetchone returns a tuple like (count,)
    return cbr_length

# Fetches the CBR for a given voter in a given election sorted by most recent votes at the top.
def fetch_CBR_for_voter_in_election(voter_id, election_id):
    conn = psycopg.connect(CONNECTION_INFO)
    cur = conn.cursor()
    cur.execute("""
                SELECT *
                FROM VoterParticipatesInElection p
                JOIN VoterCastsBallot c 
                ON p.ElectionID = c.ElectionID AND p.VoterID = c.VoterID
                JOIN Ballots b
                ON b.ID = c.BallotID
                WHERE p.ElectionID = %s AND p.VoterID = %s
                ORDER BY c.VoteTimestamp DESC;
                """, (election_id, voter_id))
    cbr = cur.fetchall()
    return cbr

def fetch_ballot_hashes(election_id):
    conn = psycopg.connect(CONNECTION_INFO)
    cur = conn.cursor()
    cur.execute("""
                SELECT BallotHash
                FROM Ballots
                Join VoterCastsBallot vcb on vcb.BallotID = Ballots.ID
                WHERE vcb.ElectionID = %s;"""
                ,(election_id,))
    ballot_hashes = cur.fetchall() # returns a list of tuples

    # Extracts the first element of each tuple
    ballothash_list = [row[0] for row in ballot_hashes]
    
    return ballothash_list

# Fetch image filename for specific ballot
def fetch_imageFilename_for_ballot(cur, ballot_id):
    cur.execute("""
                SELECT ImageFilename
                FROM Images 
                WHERE BallotID = %s
                """, (ballot_id,))
    records = cur.fetchall()
    return records