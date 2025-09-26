import json
from datetime import date
import psycopg

def date_restrictions(s: str) -> date:
    try:
        return date.fromisoformat(s)
    except Exception as e:
        raise ValueError(f"Invalid date '{s}': {e}")


def fetchElectionData(election1: str, dsn: str = "dbname=bb user=bb password=BBpass host=localhost port=5432"):

    #opens file for reading = r
    with open(election1, "r", encoding="utf-8") as f:
        payload = json.load(f)

#for now if candidates or voters are missing substitute with empty list, might be changed later
    if "election" not in payload:
        raise ValueError("JSON is missing election details")
    if "candidates" not in payload:
        payload["candidates"] = []
    if "voters" not in payload:
        payload["voters"] = []

    #normalize election fields + candidates + voters
    #pulls the election dict out
    e = payload["election"]
    eid = int(e["id"])
    ename = str(e["name"])
    estart = date_restrictions(e["start"])
    eend = date_restrictions(e["end"])

    #normalizes and builds new list of dicts
    candidates = [
        {"id": int(c["id"]), "name": str(c["name"])}
        for c in payload["candidates"]
    ]

    voters = [
        {"id": int(v["id"]), "name": str(v["name"])}
              for v in payload["voters"]
    ]


    #SQL statements
    #if row with same id exists
    sql_insert_election = """
        INSERT INTO Elections (ID, Name, ElectionStart, ElectionEnd)
        VALUES (%s, %s, %s, %s)
        ON CONFLICT (ID) DO NOTHING;
    """

    #CHECK: DOES SAME CANDIDATE HAVE SAME ID FOR TWO DIFFERETN ELECTIONS? what if id exists?
    sql_insert_candidate = """
        INSERT INTO Candidates (ID, Name)
        VALUES (%s, %s)
        ON CONFLICT (ID) DO NOTHING;
    """

    sql_link_candidate_runs = """
        INSERT INTO CandidateRunsInElection (CandidateID, ElectionID)
        VALUES (%s, %s)
        ON CONFLICT (CandidateID, ElectionID) DO NOTHING;
    """

    sql_insert_voter = """
        INSERT INTO Voters (ID, Name)
        VALUES (%s, %s)
        ON CONFLICT (ID) DO NOTHING;
    """

    # requires PublicKey/SecretKey to be nullable or removed from schema for now
    sql_insert_voter_participation = """
        INSERT INTO VoterParticipatesInElection (VoterID, ElectionID)
        VALUES (%s, %s)
        ON CONFLICT (VoterID, ElectionID) DO NOTHING;
    """

    with psycopg.connect(dsn) as conn:
        with conn.cursor() as cur:
            cur.execute(sql_insert_election, (eid, ename, estart, eend)) #insert election data, sub. vaule into %s

            #loops over candidates, inserts each c and then inserts the relation to current election
            for c in candidates:
                cur.execute(sql_insert_candidate, (c["id"], c["name"]))
                cur.execute(sql_link_candidate_runs, (c["id"], eid))

            # loops over voters, inserts each v and then insert their participation relation row for this election
            for v in voters:
                cur.execute(sql_insert_voter, (v["id"], v["name"]))
                cur.execute(sql_insert_voter_participation, (v["id"], eid))

    if __name__ == "__main__":
        import argparse
        p = argparse.ArgumentParser(description="Load election JSON into the database.")
        p.add_argument("file", help="Path to election JSON file")
        p.add_argument("--dsn", default="dbname=bb user=bb password=BBpass host=localhost port=5432",
                   help="psycopg DSN string")
        args = p.parse_args()

        fetchElectionData(args.file, dsn=args.dsn)
        print("Election data loaded.")
