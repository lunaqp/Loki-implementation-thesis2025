import numpy as np
from datetime import datetime, timezone
import httpx
import duckdb
import asyncio

duckdb_lock = asyncio.Lock()

async def fetch_electiondates_from_bb(election_id):
    payload = {"electionid": election_id}
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post("http://bb_api:8000/send-election-startdate", json=payload)
            response.raise_for_status() # gets http status code

            election_start = datetime.fromisoformat(response.json().get("startdate")) # recreate datetime object from iso 8601 format.
            election_end = datetime.fromisoformat(response.json().get("enddate"))

        return election_start, election_end
    except Exception as e:
        print(f"Error fetching election start date: {e}")

# Generating the total amount of votes for a single voter based on a discrete uniform distribution
def generate_voteamount():

    generator = np.random.default_rng(seed=None)

    # Discrete uniform distribution from 800-1200. Size=None means that a single value is returned.
    voteamount = generator.integers(low=800, high=1200, size=None, dtype=np.int64, endpoint=True) # endpoint=true makes both low and high inclusive. Range is therefore 800-1200.
    print(voteamount)

    return voteamount

def generate_epochs(election_duration_secs, voteamount):
    # Parameters for generating a gaussian/normal distribution
    center = election_duration_secs/voteamount # Center of curve found by determining the average needed epoch length to take up the whole of the election duration.
    spread = (center * 2) / 6 # Spread of curve to ensure 99.7 percent of the values are within three standard deviations of the mean (center).
    epoch_array = np.array([])

    # Generator for creating normal distribution.
    generator = np.random.default_rng(seed=None)
    
    # We ensure we add to the epoch_array until the entire election duration is covered.
    while np.sum(epoch_array) < election_duration_secs:
        samples = generator.normal(center, spread, size=voteamount+100) # + 100 to create a buffer in case some values fall outside of the three standard deviations.

        # Loop to ensure we only keep values over 0 seconds and less than twice the mean/center.
        for interval in samples:
            if interval > 0 and interval < center * 2:
                epoch_array = np.append(epoch_array, interval)
        
    return epoch_array

# Generate timestamps for entire election for one voter
async def generate_timestamps(election_id):
    # Calculate duration of election
    start, end = await fetch_electiondates_from_bb(election_id) # fetches startdate from database.
    first_timestamp = start.timestamp()
    election_duration = end-start
    election_duration_days = election_duration.days # NOTE: Might not be needed. Depends on whether we want to increase vote amount based on election length.
    election_duration_secs = election_duration.total_seconds() # calculating election duration in seconds.
    print(f"election duration = {election_duration}")
    print(f"election duration in seconds = {election_duration_secs}")

    # Generates total number of votes for a single voter.
    voteamount = generate_voteamount()

    #TODO: pass election duration and the total number of votes for the given voter to dynamically generate epochs.
    epoch_array = generate_epochs(election_duration_secs, voteamount)

    # Adding timestamps to a timeline for the 24 hours the election lasts.
    # sum is used to track on 24-hour timeline:    0 sec |--------------------------------------| 86400 sec
    sum = 0
    timestamps = [first_timestamp]
    for epoch in epoch_array:
        sum = sum + epoch
        if sum > election_duration_secs:
            sum = election_duration_secs
            last_timestamp = first_timestamp + sum
            timestamps.append(last_timestamp)
            break
        timestamp = first_timestamp + sum
        timestamps.append(timestamp)

    # Print for troubleshooting
    for timestamp in timestamps:
        dt = datetime.fromtimestamp(timestamp, tz=timezone.utc)
        print(dt)

    return timestamps

async def save_timestamps_for_voter(election_id, voter_id):
    try:
        timestamps = await generate_timestamps(election_id) # returns array of timestamps.
        await save_timestamps_to_db(election_id, voter_id, timestamps) 

    except Exception as e:
        print(f"Error saving timestamps for voter {voter_id} in election {election_id}: {e}")

async def save_timestamps_to_db(election_id, voter_id, timestamps):
    print(f"Writing timestamps to Duckdb for voter {voter_id}")
    try:
        async with duckdb_lock: # lock is acquired to check if access should be allowed, lock while accessing ressource and is then released before returning  
            conn = duckdb.connect("/duckdb/voter-timestamps.duckdb")
            print("inserting data in duckdb")
            for timestamp in timestamps:
                dt_timestamp = datetime.fromtimestamp(timestamp, tz=timezone.utc) # convert to datetime to store in DB as TIMESTAMPTZ
                conn.execute(f"INSERT INTO VoterTimestamps VALUES (?, ?, ?, ?)", (voter_id, election_id, dt_timestamp, False))
    except Exception as e:
        print(f"error writing to duckdb for voter {voter_id} in election {election_id}: {e}")

async def fetch_ballot0_timestamp(election_id, voter_id):
    try:
        async with duckdb_lock: # lock is acquired to check if access should be allowed, lock while accessing ressource and is then released before returning  
            conn = duckdb.connect("/duckdb/voter-timestamps.duckdb")
            print("fetching first timestamp from duckdb")
            (ballot0_timestamp,) = conn.execute("""
                    SELECT Timestamp
                    FROM VoterTimestamps
                    WHERE VoterID = ? AND ElectionID = ?
                    ORDER BY Timestamp ASC
                    LIMIT 1
                    """, (voter_id, election_id)).fetchone()
            
            # Set processed column to true for the fetched timestamp:
            conn.execute("""
                UPDATE VoterTimestamps
                SET Processed = TRUE
                WHERE VoterID = ? AND ElectionID = ? AND Timestamp = ?
            """, (voter_id, election_id, ballot0_timestamp))

            return ballot0_timestamp
    except Exception as e:
        print(f"error fetching timestamp from duckdb for voter {voter_id} in election {election_id}: {e}")

