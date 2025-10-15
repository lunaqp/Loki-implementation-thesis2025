import psycopg
import os
from models import NewElectionData

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