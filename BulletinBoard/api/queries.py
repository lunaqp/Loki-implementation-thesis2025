import psycopg
import os

DBNAME = os.getenv("POSTGRES_DB", "postgres")
DBUSER = os.getenv("POSTGRES_USER", "postgres")
DBPASSWORD = os.getenv("POSTGRES_PASSWORD", "appdb")
DBHOST = os.getenv("POSTGRES_HOST", "db")
DBPORT = os.getenv("POSTGRES_PORT", "5432")

# After having created a postgres database and connected a new user to it, establish connection with the relevant info inserted below:
conn = psycopg.connect(dbname=DBNAME, user=DBUSER, password=DBPASSWORD, host=DBHOST, port=DBPORT)

# Open a cursor to perform database operations
cur = conn.cursor()

# Query for fetching all candidates running in a given election id:
def fetch_candidates_for_election(election_id): # Should cursor be given as parameter?
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

# Query for fetching all election data
def fetch_all_elections(cur):
    cur.execute("""
                SELECT *
                FROM Elections
                """)
    records = cur.fetchall()
    return records

# Query for fetching all voters participating in a given election
def fetch_voters_for_election(cur, election_id):
    cur.execute("""
                SELECT *
                FROM Voters v
                Join VoterParticipatesInElection ve on v.ID = ve.VoterID
                WHERE ve.ElectionID = %s;"""
                ,(election_id,))
    records = cur.fetchall()
    return records
    
# Fetches the CBR for a given voter in a given election sorted by most recent votes at the top.
def fetch_CBR_for_voter_in_election(cur, voter_id, election_id): # We currently also gets the voters public and private keys. Do we want to move this to the Voter table?
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
    records = cur.fetchall()
    return records

# Fetch image filename for specific ballot
def fetch_imageFilename_for_ballot(cur, ballot_id):
    cur.execute("""
                SELECT ImageFilename
                FROM Images 
                WHERE BallotID = %s
                """, (ballot_id,))
    records = cur.fetchall()
    return records