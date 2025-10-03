from __future__ import annotations
import os, json, argparse
from datetime import date
from typing import List 
import psycopg
from pydantic import BaseModel #base for requests/respone data models

#NOTE:
#Call/load new election file without FastApi: docker exec -it loki-implementation-thesis2025-ra_api-1 python /app/fetchNewElection.py /app/data/election1.json
#Call/load new election file with FastApi:  "Invoke-RestMethod -Uri "http://localhost:8002/elections/load-file?name=election1.json" -Method Post" in terminal
#to remove data from db: docker volume rm loki-implementation-thesis2025_db_data

#Configure environment
#pulls connection pieces from env variables, DNS composes these into psycopg connection string
DB_NAME = os.getenv("POSTGRES_DB", "appdb")
DB_USER = os.getenv("POSTGRES_USER", "postgres")
DB_PASS = os.getenv("POSTGRES_PASSWORD", "postgres")
DB_HOST = os.getenv("POSTGRES_HOST", "db")  # docker service name
DB_PORT = int(os.getenv("POSTGRES_PORT", "5432"))
CONNECTION_INFO = f"dbname={DB_NAME} user={DB_USER} password={DB_PASS} host={DB_HOST} port={DB_PORT}" # all info that psycopg needs to connect to db

DATA_DIR = os.getenv("DATA_DIR", "/app/data") #this is the electionData dir

#pydandic models: when data is parsed to this model, it make automatic input validation and raises errors if fiels are missing or wrong
#pydandic: converts string "123" into int.parsing dates.
#Declares shape and type of the data object. ex. candidates: id, name
class Candidate(BaseModel):
    id: int
    name: str

class Voter(BaseModel):
    id: int
    name: str

class Election(BaseModel):
    id: int
    name: str
    start: date #should be ISO format
    end: date

#Defines whole request loader expects
class NewElectionData(BaseModel):
    election: Election
    candidates: List[Candidate] = []
    voters: List[Voter] = []

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

#Load data to db
def load_election_into_db(payload: NewElectionData, connection_info: str = CONNECTION_INFO) -> None:

    #Writes the election, candidates, voters and relations to the DB.
    eid = payload.election.id

    with psycopg.connect(connection_info) as conn:
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

    
#This is to load into DB directly not via fastapi    
# if __name__ == "__main__":
#     p = argparse.ArgumentParser(description="Load an election JSON into Postgres.") #creates commandline parser
#     p.add_argument("file", help="Path to election JSON (inside container or host)")#adds positional arg file you must pass, e.g. election1.json
#     p.add_argument("--use-data-dir", action="store_true",
#                    help="Prepend DATA_DIR to the file name (useful in Docker)")
#     args = p.parse_args() #parses command line arguments into args object.

#     path = os.path.join(DATA_DIR, args.file) if args.use_data_dir else args.file #computes actual file path to read
#     if not os.path.isfile(path):
#         raise SystemExit(f"File not found: {path}")

#     with open(path, "r", encoding="utf-8") as f: #opens json file and parse into python dict raw
#         raw = json.load(f) 
#     payload = NewElectionData.model_validate(raw) #pydandic validates and turns raw into typed NewElectionData object
#     load_election_into_db(payload) #calls loader to write election to db
#     print(f"Loaded election {payload.election.id} from {path}")
