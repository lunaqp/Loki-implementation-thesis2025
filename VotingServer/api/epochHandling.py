from datetime import datetime, timezone
import httpx
import duckdb
import asyncio
from datetime import datetime
import os, glob, random
from epochGeneration import duckdb_lock, round_seconds_timestamps


current_time = datetime.now()

async def update_time():
    global current_time
    while True:
        current_time = round_seconds_timestamps(datetime.now())
        print(current_time)
        await asyncio.sleep(1)


async def fetch_next_timestamp_for_voter(voter_id, election_id):
    try:
        async with duckdb_lock: # lock is acquired to check if access should be allowed, lock while accessing ressource and is then released before returning  
            conn = duckdb.connect("/duckdb/voter-timestamps.duckdb")
            voter_id, timestamp = conn.execute("""
                    SELECT VoterID, Timestamp
                    FROM VoterTimestamps
                    WHERE ElectionID = ? AND Processed = false
                    ORDER BY ASC
                    LIMIT 1
                    """, (voter_id, election_id)).fetchone()
            
            return voter_id, timestamp
    except Exception as e:
        print(f"error fetching next timestamp from duckdb for voter {voter_id} in election {election_id}: {e}")


