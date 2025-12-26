"""
This module provides utilities for modelling voter CBRs, such as for generating
the number of ballots, defining the epochs between them, defining timestamps at
which the Voting Server should cast the ballots, and finally assigning an image
to each ballot.

It generates:
- A randomized number of ballots per voter using a discrete uniform distribution
- Time intervals (epochs) between ballots based on a normal distribution
- Timestamp sequences spanning an entire election period
- Randomized image assignments corresponding to ballot timestamps

The primary goal is to perform necessary preperations before an election starts.
"""
import numpy as np
import random

def assign_images_for_timestamps(length: int):
    """
    Assign image paths to timestamps for a single voter.

    This function reads image paths from a text file, shuffles them to ensure
    randomness per voter, and returns a list of image paths with the specified
    length matching the total number of timestamps. Supports up to a length of
    1100.

    Args:
        length (int): Number of image paths to return (one per timestamp).

    Returns:
        list[str]: A shuffled list of image paths of length `length`,
        matching the number of timestamps.
    """

    with open("/app/images.txt", "r", encoding="utf-8") as f:
        imgs = [line.strip() for line in f if line.strip()]

    random.shuffle(imgs)
    return [p for _, p in zip(range(length), imgs)] #Creates an infinite repeating iterator of images, pairs it with a length, takes second element from each pair(img path) and builds a list


# Generating the total amount of votes for a single voter based on a discrete uniform distribution
def generate_voteamount():
    """
    Generate the initial ballot amount for a single voter.

    The number of ballots is drawn from a discrete uniform distribution.
    The low and high end of the distribution can be adjusted so that it
    matches the election length.

    Returns:
        numpy.int64: The number of ballots assigned to a voter.
    """
    generator = np.random.default_rng(seed=None)

    # Discrete uniform distribution (inclusive of both low and high). Size=None ensures that a single value is returned.
    voteamount = generator.integers(low=18, high=20, size=None, dtype=np.int64, endpoint=True) # endpoint=true makes both low and high inclusive.
    return voteamount

def generate_epochs(election_duration_secs, voteamount):
    """
    Generate time intervals (epochs) between ballots on CBR for a voter.

    Epochs are sampled from a normal (Gaussian) distribution that has a
    center calculated based on election-duration and voteamount to ensure
    a mean that ideally spans the entire election duration when summed.
    Intervals are filtered to ensure realistic spacing between ballots.

    Args:
        election_duration_secs (float): Total election duration in seconds.
        voteamount (int): Number of initial ballots for the voter.

    Returns:
        numpy.ndarray: An array of epoch durations (in seconds).
    """
    # Parameters for generating a gaussian/normal distribution
    center = election_duration_secs/voteamount # Center of curve found by determining the average needed epoch length to take up the whole of the election duration.
    spread = (center * 2) / 6 # Spread of curve/standard deviation chosen so ~99.7% of values fall within [0, 2 * center] (three standard deviations from mean).
    epoch_array = np.array([])

    # Generator for creating normal distribution.
    generator = np.random.default_rng(seed=None)
    
    # Continue sampling until total election duration is covered
    while np.sum(epoch_array) < election_duration_secs:
        samples = generator.normal(center, spread, size=voteamount+100) # + 100 to create a buffer in case some values fall outside of the three standard deviations.

        # Loop to ensure we only keep values over 5 seconds and less than twice the mean/center.
        for interval in samples:
            if interval >= 5 and interval < center * 2: # minimum time of 5 seconds to ensure certain amount of time between timestamps.
                epoch_array = np.append(epoch_array, interval)
        
    return epoch_array

async def generate_timestamps(start, end):
    """
    Generate a list of timestamps for a single voter, representing when
    ballots are sent to the Bulletin Board by the Voting Server.

    Timestamps are created by cumulatively summing generated epochs,
    starting from the election start time and ending at or before the
    election end time.

    Args:
        start (datetime.datetime): Election start time.
        end (datetime.datetime): Election end time.

    Returns:
        list[float]: A list of UNIX timestamps representing vote times.
    """
    # Calculate duration of election
    first_timestamp = start.timestamp() # Convert start time to a UNIX timestamp
    election_duration = end-start
    election_duration_secs = election_duration.total_seconds() # calculating election duration in seconds.

    # Generates total number of votes for a single voter.
    voteamount = generate_voteamount()

    # Epochs are generated dynamically based on election duration and the total number of ballots for the given voter.
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