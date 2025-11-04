import numpy as np
from datetime import datetime, timezone, timedelta
import httpx
import duckdb
import asyncio
import os, glob, random
from itertools import cycle
from coloursVS import RED, CYAN

duckdb_lock = asyncio.Lock()
IMG_DIR = "/images" #where img are located, defined in docker compose

def load_image_paths(img_dir: str = IMG_DIR):
    paths = glob.glob(os.path.join(img_dir, "*.jpg")) #Use Python glob module to search for files that match pattern *.jpg inside the img_dir
    if not paths:
        raise RuntimeError(f"{RED}No images found in {img_dir}")
    return paths #return list of img paths

#NOTE: Remove cycle once we have images enough
def assign_images_for_timestamps(length: int): #assigns imgs, returns list of length x imgpaths, one per timestamp
    #Return list of image paths length, shuffled for each voter. If fewer images than length, cycle through.
    #imgs = load_image_paths()
    imgs = ["a", "b", "c", "d", "e", "f"]
    random.shuffle(imgs)
    return [p for _, p in zip(range(length), cycle(imgs))] #Creates an infinite repeating iterator of images, pairs it with a length, takes second element from each pair(img path) and builds a list


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
        print(f"{RED}Error fetching election start date: {e}")

# Generating the total amount of votes for a single voter based on a discrete uniform distribution
def generate_voteamount():

    generator = np.random.default_rng(seed=None)

    # Discrete uniform distribution from 900-1100. Size=None means that a single value is returned.
    voteamount = generator.integers(low=10, high=15, size=None, dtype=np.int64, endpoint=True) # endpoint=true makes both low and high inclusive. Range is therefore 800-1200.

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
            if interval > 5 and interval < center * 2: #NOTE: minimum time = 5 sec buffer. To ensure certain amount of time between timestamps.
                epoch_array = np.append(epoch_array, interval)
        
    return epoch_array

# Generate timestamps for entire election for one voter
async def generate_timestamps(election_id):
    # Calculate duration of election
    start, end = await fetch_electiondates_from_bb(election_id) # fetches startdate from database.
    first_timestamp = start.timestamp()
    election_duration = end-start
    election_duration_secs = election_duration.total_seconds() # calculating election duration in seconds.

    # Generates total number of votes for a single voter.
    voteamount = generate_voteamount()

    # pass election duration and the total number of votes for the given voter to dynamically generate epochs.
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

    return timestamps

def round_seconds_timestamps(ts: datetime) -> datetime:
    if ts.microsecond >= 500_000:
        ts += timedelta(seconds = 1)

    return ts.replace(microsecond = 0)

async def create_timestamps(ballot0list, election_id):
<<<<<<< Updated upstream
    for ballot in ballot0list:
        await save_timestamps_for_voter(election_id, ballot.voterid)
=======
    voter_timestamps = []
    for ballot in ballot0list:
        voter_timestamps.append(await generate_timestamps_for_voter(election_id, ballot.voterid))
>>>>>>> Stashed changes

    await save_timestamps_to_db(election_id, voter_timestamps) 

async def generate_timestamps_for_voter(election_id, voter_id):
    try:
        timestamps = await generate_timestamps(election_id) # returns array of timestamps.
        _, end = await fetch_electiondates_from_bb(election_id)
        last_timestamp = end.timestamp() + 60
        print(f"last timestamp: {last_timestamp}")
        timestamps.append(last_timestamp)
        print(f"timestamps: {timestamps}")
        return (voter_id, timestamps)

    except Exception as e:
        print(f"{RED}Error saving timestamps for voter {voter_id} in election {election_id}: {e}")


async def save_timestamps_to_db(election_id, voter_timestamps):
    print(f"{CYAN}Writing timestamps to Duckdb for election {election_id}")
    try:
        async with duckdb_lock: # lock is acquired to check if access should be allowed, lock while accessing ressource and is then released before returning  
            conn = duckdb.connect("/duckdb/voter-data.duckdb")
            for voter_id, timestamps in voter_timestamps:
                print(f"voterid: {voter_id}, timestamps length: {len(timestamps)}")
                image_paths = assign_images_for_timestamps(len(timestamps))
                rows = [] #list to collect all rows we want to insert in DB in one batch
                for timestamp, img in zip(timestamps, image_paths):
                    dt_timestamp = datetime.fromtimestamp(timestamp, tz=timezone.utc) # convert to datetime to store in DB as TIMESTAMPTZ
                    timestamp_rounded = round_seconds_timestamps(dt_timestamp)
                    rows.append((voter_id, election_id, timestamp_rounded, False, img))
                conn.executemany("INSERT INTO VoterTimestamps (VoterID, ElectionID, Timestamp, Processed, ImagePath) VALUES (?, ?, ?, ?, ?)", rows) #inserts all rows in one operation
        conn.close()
    except Exception as e:
        print(f"{RED}error writing to duckdb for voter {voter_id} in election {election_id}: {e}")

async def fetch_ballot0_timestamp(election_id, voter_id):
    try:
        async with duckdb_lock: # lock is acquired to check if access should be allowed, lock while accessing ressource and is then released before returning  
            conn = duckdb.connect("/duckdb/voter-data.duckdb")
            ballot0_timestamp, image_path = conn.execute("""
                    SELECT Timestamp, ImagePath
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

            return ballot0_timestamp, image_path
    except Exception as e:
        print(f"{RED}error fetching timestamp from duckdb for voter {voter_id} in election {election_id}: {e}")


async def fetch_ballot_timestamp_and_imagepath(election_id, voter_id):
    try:
        async with duckdb_lock: # lock is acquired to check if access should be allowed, lock while accessing ressource and is then released before returning  
            conn = duckdb.connect("/duckdb/voter-data.duckdb")
            ballot_timestamp, image_path = conn.execute("""
                    SELECT Timestamp, ImagePath
                    FROM VoterTimestamps
                    WHERE VoterID = ? AND ElectionID = ? AND Processed = false
                    ORDER BY Timestamp ASC
                    LIMIT 1
                    """, (voter_id, election_id)).fetchone()
            
            # Set processed column to true for the fetched timestamp:
            conn.execute("""
                UPDATE VoterTimestamps
                SET Processed = TRUE
                WHERE VoterID = ? AND ElectionID = ? AND Timestamp = ?
            """, (voter_id, election_id, ballot_timestamp))

            return ballot_timestamp, image_path
    except Exception as e:
        print(f"{RED}error fetching timestamp from duckdb for voter {voter_id} in election {election_id}: {e}")

