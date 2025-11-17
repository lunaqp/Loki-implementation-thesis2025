"""This file has all database calls for the Bulletin Board.

It handles all "read" and "write" operations to the PostgreSQL database.
"""

import os
from modelsBB import NewElectionData, VoterKeyList, Ballot, ElectionResult, Elections, Election, IndexImageCBR, IndexImage, CandidateResult
import base64
from hashBB import hash_ballot
import json
from psycopg_pool import ConnectionPool


DB_NAME = os.getenv("POSTGRES_DB", "appdb")
DB_USER = os.getenv("POSTGRES_USER", "postgres")
DB_PASS = os.getenv("POSTGRES_PASSWORD", "postgres")
DB_HOST = os.getenv("POSTGRES_HOST", "db")  # docker service name
DB_PORT = int(os.getenv("POSTGRES_PORT", "5432"))
CONNECTION_INFO = f"dbname={DB_NAME} user={DB_USER} password={DB_PASS} host={DB_HOST} port={DB_PORT}" # all info that psycopg needs to connect to db

pool = ConnectionPool(conninfo=CONNECTION_INFO, open=True)

## ---------------- WRITING TO DB ---------------- ##
#SQL statements for insertion/ updating

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
    """Load a newly received election + election related data.

    Writes election with its candidates, and voters to the database.
    "Candidate runs in election" relationships are also created.
    Args:
        payload (NewElectionData): Pydantic model containing election info,
            participating candidates, and voters.
    """
    eid = payload.election.id

    with pool.connection() as conn:
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
    """Loads a ballot and the ballots relations to the DB.

    The ballot ciphertexts, proof and hash are stored in the "Ballots" table,
    and the relationship between voter, election, and ballot is stored
    in the "VoterCastsBallot" relation. The corresponding image filename related to the ballot is stored
    in the "Images" table.
    Args:
        pyBallot (Ballot): Pydantic model representing a ballot.
    """

    election_id = pyBallot.electionid
    ctv = json.dumps(pyBallot.ctv) # json string of base64 encoding
    ctlv = json.dumps(pyBallot.ctlv)
    ctlid = json.dumps(pyBallot.ctlid)
    proof = base64.b64decode(pyBallot.proof)
    
    hashed_ballot = hash_ballot(pyBallot) 
    timestamp = pyBallot.timestamp

    with pool.connection() as conn:
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

def save_elgamalparams(GROUP, GENERATOR, ORDER):
    """Load elgamal group parameters to the database for an election after receiving them from RA.
    Args:
        GROUP: Description or id of the group/curve.
        GENERATOR (bytes): Group generator in binary form.
        ORDER (bytes): Group order in binary form.
    """
    with pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                        UPDATE GlobalInfo
                        SET GroupCurve = %s, Generator = %s, OrderP = %s
                        WHERE ID = 0
                        """, (GROUP, GENERATOR, ORDER))


def save_key_to_db(service, KEY):
    """Load the public key of TS or VS to the DB.
    Args:
        service (str): Service id, values are "TS" or "VS".
        KEY (bytes): Public key of servise in binary format.
    """
    if service == "TS":
        column = "PublicKeyTallyingServer"
    elif service == "VS":
        column = "PublicKeyVotingServer"
        
    with pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute(f"""
                        UPDATE GlobalInfo
                        SET {column} = %s
                        WHERE ID = 0
                        """, (KEY,))


def save_voter_keys_to_db(voter_key_list: VoterKeyList):
    """Load public key material for each voter in an election to DB.
    Args:
        voter_key_list (VoterKeyList): List of voter keys containing
            election id, voter id, and Base64-encoded public keys.
    """
    voter_keys : list = voter_key_list.voterkeylist
    with pool.connection() as conn:
        with conn.cursor() as cur:
            for voter_key in voter_keys:
                cur.execute("""
                            INSERT INTO VoterParticipatesInElection (ElectionID, VoterID, PublicKey)
                            VALUES (%s, %s, %s)
                            """, (voter_key.electionid, voter_key.voterid, base64.b64decode(voter_key.publickey))) # Decode base64 to retrieve byte object


def save_election_result(election_result: ElectionResult):
    """Load tally results and proofs for an election.
    For each candidate in the election, the final vote count and tally proof are saved in the
    "CandidateRunsInElection" table.
    Args:
        election_result (ElectionResult): Pydantic model containing result an proof for each specific candidate in election.
    """
    election_id = election_result.electionid
    
    # Looping through all candidates to store the votecount and the proof for each candidate individually.
    for candidate in election_result.result:
        candidate_id = candidate.candidateid
        vote_count = candidate.votes
        proof_bin = base64.b64decode(candidate.proof)  # decoding proof to store as binary
    
        with pool.connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                            UPDATE CandidateRunsInElection
                            SET Result = %s, Tallyproof = %s
                            WHERE (ElectionID = %s AND CandidateID = %s)
                            """, (vote_count, proof_bin, election_id, candidate_id) 
                            )

## ---------------- READING FROM DB ---------------- ##
#Calls to fetch/read from DB

async def fetch_params():
    """Fetch elgamal parameters from the DB.
    Returns:
        (GROUP, GENERATOR, ORDER) where GENERATOR and ORDER are bytes.
    """
    with pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                        SELECT GroupCurve, Generator, OrderP
                        FROM GlobalInfo
                        WHERE ID = 0
                    """)
            (GROUP, GENERATOR, ORDER) = cur.fetchone()
    return GROUP, GENERATOR, ORDER

def fetch_voters_for_election(election_id):
    """Fetch all voters participating in a given election.
    Args:
        election_id: Id of the election.
    Returns:
        list[tuple]: List of (id and name) for voters.
    """
    with pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                        SELECT v.ID, v.Name
                        FROM Voters v
                        Join VoterParticipatesInElection ve on v.ID = ve.VoterID
                        WHERE ve.ElectionID = %s;"""
                        ,(election_id,))
            records = cur.fetchall()
    return records

def fetch_candidates_for_election(election_id): # Should cursor be given as parameter?
    """Fetch all candidates running in a given election.
    Args:
        election_id: Id of the election.
    Returns:
        list[tuple]: List of (id and name) for candidates.
    """
    with pool.connection() as conn:
        with conn.cursor() as cur:
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

def fetch_election_dates(election_id):
    """Fetch election start and end dates from DB.
    Args:
        election_id: Id of the election.
    Returns:
        (ElectionStart, ElectionEnd) as datetime objects.
    """
    with pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                        SELECT ElectionStart, ElectionEnd
                        FROM Elections
                        WHERE ID = %s
                        """, (election_id,))
            election_startdate, election_enddate = cur.fetchone()
    return election_startdate, election_enddate

def fetch_public_keys_tsvs():
    """Fetch public keys for the Tallying Server and Voting Server.
    Returns:
        tuple: (public_key_ts_bin, public_key_vs_bin) as binary.
    """
    with pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                        SELECT PublicKeyTallyingServer, PublicKeyVotingServer
                        FROM GlobalInfo
                        WHERE ID = 0
                        """)
            public_key_ts_bin, public_key_vs_bin = cur.fetchone()

    return public_key_ts_bin, public_key_vs_bin

def fetch_voter_public_key(voter_id, election_id):
    """Fetch public key of a specific voter in a given election.
    Args:
        voter_id: Id of the voter.
        election_id: Id of the election.
    Returns:
        Public key in binary format.
    """
    with pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                        SELECT PublicKey
                        FROM VoterParticipatesInElection
                        WHERE VoterID = %s AND ElectionID = %s;
                        """, (voter_id, election_id))
            (upk,) = cur.fetchone()
            
    return upk

def fetch_last_and_previouslast_ballot(voter_id, election_id):
    """Fetch the last and previous last ballots for a voter in an election.
    Args:
        voter_id: Id of the voter.
        election_id: Id of the election.
    Returns:
        tuple: (last_ballot_b64, previous_last_ballot_b64) where each ballot is
            represented as a tuple of base64-encoded ciphertexts and proof.
            Second element is None if only one ballot exists.
    """
    with pool.connection() as conn:
        with conn.cursor() as cur:
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
    
    # base64 encoding NIZK proof:
    proof_b64 = base64.b64encode(ballot_ct[3]).decode()
    return (ct_v_b64, ct_lv_b64, ct_lid_b64, proof_b64)

def fetch_cbr_length(voter_id, election_id):
    with pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                        SELECT COUNT(*)
                        FROM VoterParticipatesInElection p
                        JOIN VoterCastsBallot c 
                        ON p.ElectionID = c.ElectionID AND p.VoterID = c.VoterID
                        WHERE p.ElectionID = %s AND p.VoterID = %s
                        """, (election_id, voter_id))
            (cbr_length,) = cur.fetchone()  # fetchone returns a tuple like (count,)
    return cbr_length

# Fetches the CBR for a given voter in a given election sorted by oldest votes at the top.
def fetch_cbr_for_voter_in_election(voter_id, election_id):
    with pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                        SELECT ImageFilename, c.VoteTimestamp
                        FROM VoterParticipatesInElection p
                        JOIN VoterCastsBallot c 
                        ON p.ElectionID = c.ElectionID AND p.VoterID = c.VoterID
                        JOIN Ballots b
                        ON b.ID = c.BallotID
                        JOIN Images i 
                        ON i.BallotID = b.ID
                        WHERE p.ElectionID = %s AND p.VoterID = %s
                        ORDER BY c.VoteTimestamp ASC;
                        """, (election_id, voter_id))
            cbr = cur.fetchall()

    cbr_images = [
        IndexImage(cbrindex=idx, image=row[0], timestamp = row[1])
        for idx, row in enumerate(cbr)
    ]

    return IndexImageCBR(cbrimages=cbr_images)

def fetch_ballot_hashes(election_id):
    with pool.connection() as conn:
        with conn.cursor() as cur:
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
    with pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                        SELECT ImageFilename
                        FROM Images 
                        WHERE BallotID = %s
                        """, (ballot_id,))
            records = cur.fetchall()
    return records

def fetch_last_ballot_ctvs(election_id):
    with pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                        SELECT DISTINCT ON (p.VoterID)
                            CtCandidate
                        FROM VoterParticipatesInElection p
                        JOIN VoterCastsBallot c 
                        ON p.ElectionID = c.ElectionID AND p.VoterID = c.VoterID
                        JOIN Ballots b
                        ON b.ID = c.BallotID
                        WHERE p.ElectionID = %s
                        ORDER BY p.VoterID, c.VoteTimestamp DESC;
                        """, (election_id,))
            rows = cur.fetchall() 

    # to only keep the first element, ctv, of each returned tuple as each tuple is returned as (ctv, )
    last_ballot_ctvs_json  = [row[0] for row in rows] 
    
    return last_ballot_ctvs_json

# Fetch elections for a given voter
def fetch_elections_for_voter(voter_id):
    with pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                        SELECT ID, Name, ElectionStart, ElectionEnd
                        FROM Elections e
                        JOIN VoterParticipatesInElection p
                        ON p.ElectionID = e.ID
                        WHERE VoterID = %s
                        """, (voter_id,))
            records = cur.fetchall()

    elections = Elections(
        elections = [Election (id=election_id, name=name, start=start, end=end) for election_id, name, start, end in records]
    ) 

    return elections


# Fetch elections for a given voter
def fetch_election_result(election_id):
    with pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                        SELECT CandidateID, Result, TallyProof
                        FROM CandidateRunsInElection 
                        WHERE ElectionID = %s
                        """, (election_id,))
            records = cur.fetchall()

    # If result is not available return None.
    if not records or any(result is None or proof is None for _, result, proof in records):
        return None

    # If result is available build and return a pydantic model.
    candidate_result: CandidateResult = []

    for candidate_id, result, proof in records:
        proof_b64 = base64.b64encode(proof).decode()
        candidate_result.append(CandidateResult (
            candidateid = candidate_id,
            votes = result,
            proof = proof_b64
        ))
    
    election_result : ElectionResult = ElectionResult (
        electionid = election_id,
        result = candidate_result
    )

    return election_result