import numpy as np
import random
from fetch_functions import fetch_electiondates_from_bb

def assign_images_for_timestamps(length: int): #assigns imgs, returns list of length x imgpaths, one per timestamp
    #Return list of image paths length, shuffled for each voter. If fewer images than length, cycle through.

    with open("/app/images.txt", "r", encoding="utf-8") as f:
        imgs = [line.strip() for line in f if line.strip()]

    random.shuffle(imgs)
    return [p for _, p in zip(range(length), imgs)] #Creates an infinite repeating iterator of images, pairs it with a length, takes second element from each pair(img path) and builds a list


# Generating the total amount of votes for a single voter based on a discrete uniform distribution
def generate_voteamount():

    generator = np.random.default_rng(seed=None)

    # Discrete uniform distribution from 900-1100. Size=None means that a single value is returned.
    voteamount = generator.integers(low=18, high=20, size=None, dtype=np.int64, endpoint=True) # endpoint=true makes both low and high inclusive.
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

        # Loop to ensure we only keep values over 5 seconds and less than twice the mean/center.
        for interval in samples:
            if interval >= 5 and interval < center * 2: # minimum time of 5 seconds to ensure certain amount of time between timestamps.
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

    # Adding timestamps to a timeline for the duration the election lasts.
    # sum is used to track progress on timeline:    0 sec |--------------------------------------| election_duration_secs
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


