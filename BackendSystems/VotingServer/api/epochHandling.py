"""
This module performs necessary preparations for upcoming elections and handles
ballot-casting throughout the election.

It is responsible for:
- Preparing elections by generating CBR ballot timestamps per voter.
- Managing asynchronous ballot casting for each voter during the election period.
- Reconstructing and validating voter-cast ballots.
- Generating obfuscating ballots.
- Sending ballots to the Bulletin Board (BB).
- Persisting and retrieving voter timestamps and pending votes using DuckDB.
- Assigning image paths to each vote timestamp.
"""
import httpx
import duckdb
import asyncio
from datetime import datetime, timezone, timedelta
from validateBallot import obfuscate, validate_ballot
from modelsVS import Ballot, BallotPayload
from fastapi import HTTPException 
import json
import pytz
from coloursVS import RED, CYAN, GREEN, PURPLE, YELLOW, PINK
from lock import duckdb_lock
from fetchFunctions import fetch_electiondates_from_bb
from epochGeneration import generate_timestamps, assign_images_for_timestamps
import time

e_time_obf_incl_network = [] # For performance measurements of obfuscation including network calls.

tz = pytz.timezone('Europe/Copenhagen')
current_time = datetime.now(tz)

async def update_time():
    """Update the global current_time variable once per second, rounded to nearest second. Runs as a background task."""
    global current_time
    while True:
        current_time = round_seconds_timestamps(datetime.now(tz))
        await asyncio.sleep(1)

async def prepare_election(payload: BallotPayload):
    """
    Prepare an election for all voters in the given payload.

    This function:
    - Generates timestamps for all voters
    - Sends ballot0 for each voter to the Bulletin Board
    - Starts asynchronous ballot-casting tasks for each voter

    Args:
        payload (BallotPayload): Payload containing ballot0 data and election ID.
    """
    await create_timestamps(payload.ballot0list, payload.electionid)

    for ballot in payload.ballot0list:
        ballot0_timestamp, image_path = await fetch_ballot0_timestamp(payload.electionid, ballot.voterid)

        pyBallot = Ballot(
            voterid = ballot.voterid,
            upk = ballot.upk,
            ctv = ballot.ctv,
            ctlv = ballot.ctlv, 
            ctlid = ballot.ctlid, 
            proof = ballot.proof,
            electionid = payload.electionid,
            timestamp = ballot0_timestamp,
            imagepath = image_path
        )
        await send_ballot0_to_bb(pyBallot)

    # After sending ballot 0 we create an asynchronous task for handling vote-casting to each voters CBR.
    start, end = await fetch_electiondates_from_bb(payload.electionid)
    for ballot in payload.ballot0list:
        asyncio.create_task(timestamp_management(ballot.voterid, payload.electionid, start, end))

async def timestamp_management(voter_id, election_id, start, end):
    """
    Manage ballot casting for a single voter over the election period.

    This coroutine waits until the election starts, then repeatedly checks
    for the next scheduled timestamp and casts ballots accordingly until
    the election ends.

    Args:
        voter_id: Identifier of the voter.
        election_id: Identifier of the election.
        start (datetime): Election start time.
        end (datetime): Election end time.
    """
    time_until_start_election = (start-current_time).total_seconds()
    print(f"{CYAN}Time until election starts: {time_until_start_election}")
    await asyncio.sleep(time_until_start_election+1) # adding one second to ensure we don't check until after election start date

    while current_time >= start and current_time <= end: 
        next_timestamp = await fetch_next_timestamp_for_voter(voter_id, election_id)

        if not next_timestamp:
            print(f"{RED}No timestamps for voter {voter_id}")
            break

        if next_timestamp > end:
            print(f"{PURPLE}Waiting for election end for voter {voter_id}")
            time_until_end = (end - current_time).total_seconds()
            await asyncio.sleep(time_until_end +1) # adding one second to ensure we are outside of the election period
            break

        time_until_next_timestamp = (next_timestamp-current_time).total_seconds()
        await asyncio.sleep(time_until_next_timestamp)

        print(f"{GREEN}Reached timestamp {next_timestamp} for voter {voter_id}")
        await cast_vote(voter_id, election_id)
        # ballot_validated = await cast_vote(voter_id, election_id)
        # if ballot_validated == False
        #   async call to frontend with voterid + ballot?
    
    if current_time > end:
        print(f"{PURPLE}election over for election {election_id}")
        print(f"{PINK}Ballot obfuscation time including network calls (avg):", round(sum(e_time_obf_incl_network)/len(e_time_obf_incl_network)/1000000,3), "ms")
        try: 
            last_obf_ballot = await obfuscate(voter_id, election_id)
            await send_ballot_to_bb(last_obf_ballot)
            print(f"{YELLOW}Final obfuscation ballot sent to bb for voter {voter_id}.")
        except Exception as e:
            print(f"{RED}Error creating/sending final obfuscation ballot for voter {voter_id}: {e}")

async def cast_vote(voter_id, election_id):
    """
    Cast a ballot for a voter at the current timestamp.

    If a pending voter-cast ballot exists in the database, it is
    validated and sent. Otherwise, an obfuscation ballot is
    generated and sent.

    Args:
        voter_id: Identifier of the voter.
        election_id: Identifier of the election.

    Returns:
        bool | None: True if a ballot was validated successfully,
        False if validation failed, or None if an error occurred.
    """
    try:
        async with duckdb_lock: # lock is acquired to check if access should be allowed, lock while accessing ressource and is then released before returning  
            conn = duckdb.connect("/duckdb/voter-data.duckdb")
            row = conn.execute("""
                    SELECT PublicKey, ctv, ctlv, ctlid, Proof
                    FROM PendingVotes
                    WHERE VoterID = ? AND ElectionID = ?
                    """, (voter_id, election_id)).fetchone()
        
        # Check DuckDB table "PendingVotes" to see if a voter-cast ballot has been received from the Voting App.
        if not row or all(x is None for x in row): # If no voter-cast ballot has been received an obfuscation ballot is sent to the BB.
            s_time_obf_incl_network = time.process_time_ns() # Performance timing for ballot obfuscation including network calls
            obf_ballot = await obfuscate(voter_id, election_id)
            e_time_obf_incl_network.append(time.process_time_ns() - s_time_obf_incl_network) # Performance timing for ballot obfuscation including network calls
            await send_ballot_to_bb(obf_ballot)
        else: # If a voter-cast ballot has been received it is validated and sent to the BB.
            public_key, ct_v, ct_lv, ct_lid, proof = row
            pyballot:Ballot = construct_ballot(voter_id, public_key, ct_v, ct_lv, ct_lid, proof, election_id)
            ballot_validated = await validate_ballot(pyballot)
            # Once ballot is constructed as a pydantic ballot and validated, the data is deleted from the DuckDB table.
            conn.execute("DELETE FROM PendingVotes WHERE VoterID = ? AND ElectionID = ?", (voter_id, election_id))
            conn.close()

            if ballot_validated:
                await send_ballot_to_bb(pyballot)
                return ballot_validated # True if validated
            else:
                return ballot_validated # False if not validated
    
    except Exception as e:
        print(f"{RED}error casting ballot for voter {voter_id}, {e}")


def construct_ballot(voter_id, public_key, ct_v, ct_lv, ct_lid, proof, election_id):
    """
    Construct a Ballot object from database fields in PendingVotes.

    JSON-encoded ciphertext fields are decoded into Python lists.

    Args:
        voter_id: Identifier of the voter.
        public_key: Voter public key.
        ct_v: JSON-encoded list of ciphertexts for ballot candidate choice.
        ct_lv: JSON-encoded list of ciphertext pair for voter-provided previous ballots list.
        ct_lid: JSON-encoded list of ciphertext pair for real previous ballots list.
        proof: Cryptographic NIZK proof verifying correct construction of the ballot.
        election_id: Identifier of the election.

    Returns:
        Ballot: Constructed pydantic ballot object.
    """
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
    """
    Fetch the next unprocessed timestamp for a voter.

    Args:
        voter_id: Identifier of the voter.
        election_id: Identifier of the election.

    Returns:
        datetime | None: Next timestamp or None if none remain.
    """
    try:
        async with duckdb_lock: # lock is acquired to check if access should be allowed, locked while accessing ressource and is then released before returning  
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
            
            (timestamp,) = row
            
            return timestamp
    except Exception as e:
        print(f"{RED}error fetching next timestamp from duckdb for voter {voter_id} in election {election_id}: {e}")


async def send_ballot_to_bb(pyBallot:Ballot):
    """
    Send a ballot to the Bulletin Board.

    Fetches the next timestamp and image-path for the ballot before sending it.

    Args:
        pyBallot (Ballot): Ballot to send.

    Returns:
        dict: JSON response from the Bulletin Board.

    Raises:
        HTTPException: If sending the ballot fails.
    """
    ballot_timestamp, image_path = await fetch_ballot_timestamp_and_imagepath(pyBallot.electionid, pyBallot.voterid)

    # Add timestamp and imagepath to the pydantic ballot data.
    pyBallot.timestamp = ballot_timestamp
    pyBallot.imagepath = image_path

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post("http://bb_api:8000/receive-ballot", content = pyBallot.model_dump_json())
            response.raise_for_status() # gets http status code
            print(f"{GREEN}ballot sent to BB for voter {pyBallot.voterid}")
            return response.json()
    except Exception as e:
        print(f"{RED}Error sending ballot: {e}")
        raise HTTPException(status_code=500, detail=f"{RED}Failed to send ballot to BB: {str(e)}") 
    

async def fetch_ballot_timestamp_and_imagepath(election_id, voter_id):
    """
    Fetch and mark the next unprocessed timestamp and image-path for a ballot.
    Progress is tracked through the database column "Processed". The next row
    with "Processed = false" is fetched and Processed is set to true afterwards.

    Args:
        election_id: Identifier of the election.
        voter_id: Identifier of the voter.

    Returns:
        tuple[datetime, str]: Timestamp and image path.
    """
    try:
        async with duckdb_lock: # lock is acquired to check if access should be allowed, locked while accessing ressource and is then released before returning  
            conn = duckdb.connect("/duckdb/voter-data.duckdb")
            # Fetch next unprocessed row (Processed = false)
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

def round_seconds_timestamps(ts: datetime) -> datetime:
    """Rounds a datetime object to the nearest second."""
    if ts.microsecond >= 500_000:
        ts += timedelta(seconds = 1)

    return ts.replace(microsecond = 0)

async def create_timestamps(ballot0list, election_id):
    """
    Generate and persist timestamps for all voters in an election.

    Args:
        ballot0list (list): List of ballot0 objects.
        election_id: Identifier of the election.
    """
    try:
        start, end = await fetch_electiondates_from_bb(election_id)
        voter_timestamps = []
        tasks = [generate_timestamps_for_voter(election_id, ballot.voterid, start, end) for ballot in ballot0list]
        voter_timestamps = await asyncio.gather(*tasks) # asterisk unpacks the list of generated timestamps for each voter
        await save_timestamps_to_db(election_id, voter_timestamps)
    except Exception as e:
        print("error creating timestamps", str(e))
       

async def generate_timestamps_for_voter(election_id, voter_id, start, end):
    """
    Generate all ballot timestamps for a single voter.

    A final timestamp beyond the election end is appended intended for
    the last obfuscation ballot.

    Args:
        election_id: Identifier of the election.
        voter_id: Identifier of the voter.
        start (datetime): Election start time.
        end (datetime): Election end time.

    Returns:
        tuple: (voter_id, list of timestamps)
    """
    try:
        timestamps = await generate_timestamps(start, end) # returns array of timestamps.
        last_timestamp = end.timestamp() + 60 # Adding a timestamp after election end to use for a last obfuscation ballot.
        timestamps.append(last_timestamp)
        return (voter_id, timestamps)

    except Exception as e:
        print(f"{RED}Error saving timestamps for voter {voter_id} in election {election_id}: {e}")


async def save_timestamps_to_db(election_id, voter_timestamps):
    """
    Persist voter timestamps and associated image-paths to DuckDB.
    Set initial state of "Processed"-column to false for all rows. 

    Args:
        election_id: Identifier of the election.
        voter_timestamps (list): List of (voter_id, timestamps) tuples.
    """
    print(f"{CYAN}Writing timestamps to Duckdb for election {election_id}")
    try:
        async with duckdb_lock: # lock is acquired to check if access should be allowed, lock while accessing ressource and is then released before returning  
            conn = duckdb.connect("/duckdb/voter-data.duckdb")
            for voter_id, timestamps in voter_timestamps:
                image_paths = assign_images_for_timestamps(len(timestamps))
                rows = [] #list to collect all rows we want to insert in DB in one batch
                print(f"timestamps matched with images: {len(timestamps)}, {len(image_paths)}")
                for timestamp, img in zip(timestamps, image_paths):
                    dt_timestamp = datetime.fromtimestamp(timestamp, tz=timezone.utc) # convert to datetime to store in DB as TIMESTAMPTZ
                    timestamp_rounded = round_seconds_timestamps(dt_timestamp) # Round to nearest second.
                    rows.append((voter_id, election_id, timestamp_rounded, False, img))
                conn.executemany("INSERT INTO VoterTimestamps (VoterID, ElectionID, Timestamp, Processed, ImagePath) VALUES (?, ?, ?, ?, ?)", rows) #inserts all rows in one operation
        conn.close()
    except Exception as e:
        print(f"{RED}error writing to duckdb for voter {voter_id} in election {election_id}: {e}")


async def send_ballot0_to_bb(pyBallot: Ballot):
    """
    Send a ballot0 to the Bulletin Board.

    Args:
        pyBallot (Ballot): Initial ballot to send.

    Returns:
        dict: JSON response from the Bulletin Board.

    Raises:
        HTTPException: If sending fails.
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post("http://bb_api:8000/receive-ballot0", content = pyBallot.model_dump_json())
            response.raise_for_status() # gets http status code
            print(f"{CYAN}ballot0 sent to BB for voter {pyBallot.voterid}")
            return response.json()
    except Exception as e:
        print(f"{RED}Error sending ballot0: {e}")
        raise HTTPException(status_code=500, detail=f"{RED}Failed to send ballot0 to BB: {str(e)}") 
    
async def fetch_ballot0_timestamp(election_id, voter_id):
    """
    Fetch timestamp and image for a voter's ballot0.
    Set column "Processed = True" in VoterTimestamps table. 

    Args:
        election_id: Identifier of the election.
        voter_id: Identifier of the voter.

    Returns:
        tuple[datetime, str]: Timestamp and image path.
    """
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

