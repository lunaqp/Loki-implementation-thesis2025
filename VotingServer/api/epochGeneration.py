import numpy as np
# import matplotlib.pyplot as plt
# import seaborn as sns
from datetime import datetime, timezone
import httpx

# TODO: Create distribution for number of votes per voter - either normal or uniform distribution

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


def generate_epochs():
    # Parameters for generating a gaussian/normal distribution
    center = 86.4 # Center of curve
    spread = 30 # Spread of curve

    epoch_array = np.array([])

    generator = np.random.default_rng(seed=None)
    
    # If sum of intervals is over 84600 seconds (24hours * 60min * 60sec) then we exceed 24 hours.
    while np.sum(epoch_array) < 84600:
        samples = generator.normal(center, spread, size=1100)

        # Loop to ensure we only keep values over 0 seconds and under 3 minutes.
        for interval in samples:
            if interval > 0 and interval < 180:
                epoch_array = np.append(epoch_array, interval)
        
    return epoch_array

# Generate timestamps for entire election for one voter
async def generate_timestamps(election_id):
    # Calculate duration of election
    start, end = await fetch_electiondates_from_bb(election_id) # fetches startdate from database.
    first_timestamp = start.timestamp()
    duration = end-start # calculating election duration in seconds.
    duration_in_seconds = duration.total_seconds()
    print(f"election duration in days = {duration}")
    print(f"election duration in seconds = {duration.total_seconds()}")

    #TODO: Calculate total votes per voter based on duration

    #TODO: pass duration/votes to dynamically generate epochs.
    epoch_array = generate_epochs()

    # Adding timestamps to a timeline for the 24 hours the election lasts.
    # sum is used to track on 24-hour timeline:    0 sec |--------------------------------------| 86400 sec
    sum = 0
    timestamps = [first_timestamp]
    for epoch in epoch_array:
        sum = sum + epoch
        if sum > duration_in_seconds:
            sum = duration_in_seconds
            last_timestamp = first_timestamp + sum
            timestamps.append(last_timestamp)
            break
        timestamp = first_timestamp + sum
        timestamps.append(timestamp)

    # Print for troubleshooting
    for timestamp in timestamps:
        dt = datetime.fromtimestamp(timestamp, tz=timezone.utc)
        print(dt)

