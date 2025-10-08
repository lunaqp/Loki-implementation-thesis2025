import numpy as np
# import matplotlib.pyplot as plt
# import seaborn as sns
from datetime import datetime, timezone
import os
import psycopg

DB_NAME = os.getenv("POSTGRES_DB", "appdb")
DB_USER = os.getenv("POSTGRES_USER", "postgres")
DB_PASS = os.getenv("POSTGRES_PASSWORD", "postgres")
DB_HOST = os.getenv("POSTGRES_HOST", "db")
DB_PORT = int(os.getenv("POSTGRES_PORT", "5432"))
CONNECTION_INFO = f"dbname={DB_NAME} user={DB_USER} password={DB_PASS} host={DB_HOST} port={DB_PORT}" # all info that psycopg needs to connect to db

conn = psycopg.connect(CONNECTION_INFO)
cur = conn.cursor()

# Fetch startdate from database for timestamp generation for each voter.
def fetch_election_start(election_id):
    cur.execute("""
                SELECT ElectionStart
                FROM Elections
                WHERE ID = %s
                """, (election_id,))
    election_startdate = cur.fetchone()
    return election_startdate[0]

# NOTE: Do we work from a fixed size of 1000 ballots per voter or do we create a uniform distribution?

def generate_epochs():
    # Parameters for generating a gaussian/normal distribution
    center = 86.4 # Center of curve
    spread = 30 # Spread of curve

    epoch_array = np.array([])

    # If sum of intervals is over 84600 seconds (24hours * 60min * 60sec) then we exceed 24 hours.
    while np.sum(epoch_array) < 84600:
        samples = np.random.normal(center, spread, size=1100)

        # Loop to ensure we only keep values over 0 seconds and under 3 minutes.
        for interval in samples:
            if interval > 0 and interval < 180:
                epoch_array = np.append(epoch_array, interval)
        
    return epoch_array

# Generate timestamps for entire election for one voter
def generate_timestamps(election_id):
    epoch_array = generate_epochs()
    date = fetch_election_start(election_id) # fetches startdate from database.
    first_timestamp = date.timestamp()

    # Adding timestamps to a timeline for the 24 hours the election lasts.
    # sum is used to track on 24-hour timeline:    0 sec |--------------------------------------| 86400 sec
    sum = 0
    timestamps = [first_timestamp]
    for epoch in epoch_array:
        sum = sum + epoch
        if sum > 86400:
            sum = 86400
            last_timestamp = first_timestamp + sum
            timestamps.append(last_timestamp)
            break
        timestamp = first_timestamp + sum
        timestamps.append(timestamp)

    # Print for troubleshooting
    for timestamp in timestamps:
        dt = datetime.fromtimestamp(timestamp, tz=timezone.utc)
        print(dt)

