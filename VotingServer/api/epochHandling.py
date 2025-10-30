from datetime import datetime, timezone
import httpx
import duckdb
import asyncio
from datetime import datetime
from validateBallot import obfuscate, validate_ballot
from epochGeneration import duckdb_lock, round_seconds_timestamps
from modelsVS import Ballot
import base64
from fastapi import HTTPException 
from epochGeneration import fetch_ballot_timestamp_and_imagepath
import json

current_time = datetime.now(timezone.utc)

async def update_time():
    global current_time
    while True:
        current_time = round_seconds_timestamps(datetime.now(timezone.utc))
        await asyncio.sleep(1)

async def timestamp_management(voter_id, election_id, start, end):
    print(f"next timestamp: {await fetch_next_timestamp_for_voter(voter_id, election_id)}")
    
    time_until_start_election = (start-current_time).total_seconds()
    print(f"delay: {time_until_start_election}")
    
    await asyncio.sleep(time_until_start_election)
    print(f"start: {start}")
    print(f"current time: {current_time}")

    while current_time >= start and current_time <= end: 
        print(f"im in loop")
        next_timestamp = await fetch_next_timestamp_for_voter(voter_id, election_id)

        if not next_timestamp:
            print(f"No timestamps for voter {voter_id}")
            break

        time_until_next_timestamp = (next_timestamp-current_time).total_seconds()
        await asyncio.sleep(time_until_next_timestamp)

        print(f"Reached timestamp {next_timestamp} for voter {voter_id}")
        await cast_vote(voter_id, election_id)
    
    if current_time > end:
        print("election over")

    
async def cast_vote(voter_id, election_id):
    try:
        async with duckdb_lock: # lock is acquired to check if access should be allowed, lock while accessing ressource and is then released before returning  
            conn = duckdb.connect("/duckdb/voter-data.duckdb")
            row = conn.execute("""
                    SELECT PublicKey, ctv, ctlv, ctlid, Proof
                    FROM PendingVotes
                    WHERE VoterID = ? AND ElectionID = ?
                    """, (voter_id, election_id)).fetchone()
        
        if not row or all(x is None for x in row):
            obf_ballot = await obfuscate(voter_id, election_id)
            await send_ballot_to_bb(obf_ballot)
        else:
            public_key, ct_v, ct_lv, ct_lid, proof = row
            pyballot:Ballot = construct_ballot(voter_id, public_key, ct_v, ct_lv, ct_lid, proof, election_id)
            ballot_validated = await validate_ballot(pyballot)
            if ballot_validated:
                conn.execute("DELETE FROM PendingVotes WHERE VoterID = ? AND ElectionID = ?", (voter_id, election_id)) 
                conn.close()
                await send_ballot_to_bb(pyballot)
                return ballot_validated #true if validated
            else:
                return ballot_validated #false if not validated

    except Exception as e:
        print(f"error, fetching pending votes: {e}")


def construct_ballot(voter_id, public_key, ct_v, ct_lv, ct_lid, proof, election_id):
    #public_key_b64 = base64.b64encode(public_key).decode()
    #proof_b64 = base64.b64encode(proof).decode()

    ctv_list = json.loads(ct_v)
    ctlv_list = json.loads(ct_lv)
    ctlid_list = json.loads(ct_lid)

    pyBallot = Ballot(
            voterid = voter_id,
            upk = public_key,
            ctv = ctv_list,
            ctlv = ctlv_list,
            ctlid = ctlid_list,
            proof = proof,
            electionid = election_id
        )
    return pyBallot


async def fetch_next_timestamp_for_voter(voter_id, election_id):
    try:
        async with duckdb_lock: # lock is acquired to check if access should be allowed, lock while accessing ressource and is then released before returning  
            conn = duckdb.connect("/duckdb/voter-data.duckdb")
            row = conn.execute("""
                    SELECT Timestamp
                    FROM VoterTimestamps
                    WHERE VoterID = ? AND ElectionID = ? AND  Processed = false
                    ORDER BY Timestamp ASC
                    LIMIT 1
            """, (voter_id, election_id)).fetchone()

            if row is None:
                return None
            
            (timestamp, ) = row
            
            return timestamp
    except Exception as e:
        print(f"error fetching next timestamp from duckdb for voter {voter_id} in election {election_id}: {e}")


async def send_ballot_to_bb(pyBallot:Ballot):
    ballot_timestamp, image_path = await fetch_ballot_timestamp_and_imagepath(pyBallot.electionid, pyBallot.voterid)

    pyBallot.timestamp = ballot_timestamp
    pyBallot.imagepath = image_path

    conn = duckdb.connect("/duckdb/voter-data.duckdb") # for printing tables when testing
    conn.table("VoterTimestamps").show() # for printing tables when testing

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post("http://bb_api:8000/receive-ballot", content = pyBallot.model_dump_json())
            response.raise_for_status() # gets http status code
            print(f"ballot sent to BB for voter {pyBallot.voterid}")
            return response.json()
    except Exception as e:
        print(f"Error sending ballot: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to send ballot to BB: {str(e)}") 


async def send_ballot0_to_bb(pyBallot: Ballot):
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post("http://bb_api:8000/receive-ballot0", content = pyBallot.model_dump_json())
            response.raise_for_status() # gets http status code
            print(f"ballot0 sent to BB for voter {pyBallot.voterid}")
            return response.json()
    except Exception as e:
        print(f"Error sending ballot0: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to send ballot0 to BB: {str(e)}")  


