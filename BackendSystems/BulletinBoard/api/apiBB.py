"""
Bulletin board(BB)

This service communicates with Registration Authority (RA), Voting Server (VS),
and Tallying Server (TS) for:
- Managing elgamal parameters
- Receiving and storing elections, ballots, and public keys
- Providing election, voter and result data
"""
from fastapi import FastAPI, Query, HTTPException
from modelsBB import ElGamalParams, NewElectionData, VoterKeyList, Ballot, ElectionResult, Elections, IndexImageCBR
import base64
import dbcalls as db
from notifications import notify_ts_vs_params_saved, notify_ra_public_key_saved
from coloursBB import RED, CYAN, GREEN, PURPLE, BLUE
from datetime import datetime

app = FastAPI()

@app.get("/health")
def health():
    """Health check endpoint.
    Returns:
        dict: object indicating that the service is running.
    """
    return{"ok": True}


@app.get("/candidates")
def candidates(election_id: int = Query(..., description = "id of the election")):
    """Retrieve candidates for a specific election.
    Args:
        election_id (int): Id of the election.
    Returns:
        A dictionary containing a list of candidates with their IDs and names.
    """
    candidates = db.fetch_candidates_for_election(election_id)
    candidates_dict = [{"id": cid, "name": name} for cid, name in candidates]
    return {"candidates": candidates_dict}


@app.get("/voters")
def voters(election_id: int = Query(..., description = "id of the election")):
    """Retrieve voters for a given election.
    Args:
        election_id (int): Id of the election.
    Returns:
        A dictionary containing a list of voters with their IDs and names.
    """
    voters = db.fetch_voters_for_election(election_id)
    voters_dict = [{"id": vid, "name": name} for vid, name in voters]
    return {"voters": voters_dict}


@app.get("/elgamalparams")
async def get_params():
    """Fetch ElGamal parameters from the database.
    Returns:
        ElGamal group parameters with generator and order encoded with Base64 for transfer.
    """
    GROUP, GENERATOR, ORDER = await db.fetch_params()

    return {
    "group": GROUP,
    "generator": base64.b64encode(GENERATOR).decode(),
    "order": base64.b64encode(ORDER).decode(),  
    }


@app.post("/receive-params")
async def receive_params(params: ElGamalParams):
    """Receive and store ElGamal parameters from Registration Authority.

    Notifies the Tallying Server and Voting Server so they can
    generate their own keypairs(they wait for the elgamal param. to be saved to BB).

    Args:
        params (ElGamalParams): ElGamal parameters with Base64-encoded fields.

    Returns:
        Status message indicating they are successful stored.
    """
    GROUP = params.group
    GENERATOR = base64.b64decode(params.generator)
    ORDER = base64.b64decode(params.order)

    print(f"{BLUE}saving Elgamal parameters to database")
    db.save_elgamalparams(GROUP, GENERATOR, ORDER)

    # Send notification to Voting Server and Tallying Server so that they can generate their own keys.
    await notify_ts_vs_params_saved()

    return {"status": "ElGamal parameters saved"}


@app.post("/receive-public-key")
async def receive_key(payload: dict):
    """Receive and store public keys for  VS or TS.
    Args:
        payload (dict): Dictionary containing:
            - "service" (str): Name of the service.
            - "key" (str): Base64-encoded public key.
    Returns:
        dict: Status message indicating successful storage of keys.
    """
    service = payload.get("service")
    KEY = base64.b64decode(payload.get("key"))
    db.save_key_to_db(service, KEY)
    print(f"{BLUE}public key received from {service} and saved to database")
    await notify_ra_public_key_saved(service)

    return {"status": f"{service} public key saved"}


@app.post("/receive-election")
async def receive_election(payload: NewElectionData):
    """Receive election data from Reg. Auth. and load it into the database.
    Args:
        payload (NewElectionData): Election data including information on:
            the election, candidates, and voters.
    Returns:
        Status message indicating successful load of new election.
    """
    db.load_election_into_db(payload)
    print(f"{CYAN}election loaded with id {payload.election.id}")
    
    return {"status": "new election loaded into database"}


@app.post("/receive-ballot0")
async def receive_ballot0(pyBallot:Ballot):
    """Receive and store an initial (Ballot0) ballot.
    Args:
        pyBallot (Ballot): Ballot object containing encrypted choices and information about the ballot.
    Returns:
        dict: Status message on successful load.
    Raises:
        HTTPException: If the ballot could not be stored.
    """
    try:
        db.load_ballot_into_db(pyBallot)
        print(f"{CYAN}Ballot0 loaded with voter id {pyBallot.voterid}")
    
        return {"status": "new ballot0 loaded into database"}
    except Exception as e:
        print(f"{RED}[BB] load_ballot0_into_db failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    

@app.post("/receive-ballot")
async def receive_ballot(pyBallot:Ballot):
    """Receive and store a ballot for voter in an election.
    Args:
        pyBallot (Ballot): Ballot object containing encrypted choices and nformation about the ballot.
    Returns:
        dict: Status message on successful load.
    Raises:
        HTTPException: If the ballot could not be stored.
    """
    try:
        db.load_ballot_into_db(pyBallot)
        print(f"{GREEN}Ballot loaded with voter id {pyBallot.voterid}, in election {pyBallot.electionid}")
    
        return {"status": "new ballot loaded into database"}
    except Exception as e:
        print(f"{RED}[BB] load_ballot_into_db failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# receives public keys for voters for a given election from RA and loads them into the database.
@app.post("/receive-voter-keys")
async def receive_voter_keys(payload: VoterKeyList):
    """Receive and store public keys from Reg. Auth. for voters in a given election.
    Args:
        payload (VoterKeyList): List of voter id's and their public keys.
    """
    print(f"{CYAN}saving voter public keys to database")
    db.save_voter_keys_to_db(payload)


@app.post("/send-election-startdate")
async def send_election_startdate(payload: dict):
    """Return the start and end dates for an election.
    Args:
        payload (dict): Dictionary containing:
            - "electionid" (int): Id of the election.
    Returns:
        dict: ISO 8601 formatted start and end dates for transfer.
    """
    election_startdate, election_enddate = db.fetch_election_dates(payload.get("electionid"))

    formatted_startdate = election_startdate.isoformat()
    formatted_enddate = election_enddate.isoformat()

    return {"startdate": formatted_startdate, "enddate": formatted_enddate}


@app.get("/send-elections-for-voter")
def send_elections_for_voter(
    voter_id: int = Query(..., description="ID of the voter")
):
    """Return elections that a given voter is eligible to participate in.
    Args:
        voter_id (int): Id of the voter.
    Returns:
        Elections: Object containing election id and name.
    """
    elections: Elections = db.fetch_elections_for_voter(voter_id) 

    return elections


@app.get("/public-keys-tsvs")
async def send_public_keys_tsvs():
    """Retrieve the public keys for the Tallying Server (TS) and Voting Server (VS).
    Returns:
        dict: Base64-encoded public keys for TS and VS.
    """
    public_key_ts_bin, public_key_vs_bin = db.fetch_public_keys_tsvs()
    public_key_ts_b64 = base64.b64encode(public_key_ts_bin)
    public_key_vs_b64 = base64.b64encode(public_key_vs_bin)
    
    return {"publickey_ts": public_key_ts_b64, "publickey_vs": public_key_vs_b64}


@app.get("/voter-public-key")
def voter_public_key(
    voter_id: int = Query(..., description="ID of the voter"),
    election_id: int = Query(..., description="ID of the election")
):
    """Return the public key of a voter for a specific election.
    Args:
        voter_id (int): Id of the voter.
        election_id (int): Id of the election.
    Returns:
        Base64-encoded public key for the given voter in the given election.
    """
    voter_public_key_bin = db.fetch_voter_public_key(voter_id, election_id)
    voter_public_key_b64 = base64.b64encode(voter_public_key_bin).decode()

    return {"voter_public_key": voter_public_key_b64}


@app.get("/last_previous_last_ballot")
def get_last_previous_last_ballot(
    election_id: int = Query(..., description="ID of the election"),
    voter_id: int = Query(..., description="ID of the voter")
):
    """Return the last and previous last ballots for a voter in an election.
    Args:
        election_id (int): Id of the election.
        voter_id (int): Id of the voter.
    Returns:
        The last and the previous last ballot for the voter in the election.
    """
    last_ballot, previous_last_ballot = db.fetch_last_and_previouslast_ballot(voter_id, election_id)

    return {"last_ballot": last_ballot, "previous_last_ballot": previous_last_ballot}


@app.get("/cbr_length")
def get_cbr_lenghth(
    election_id: int = Query(..., description="ID of the election"),
    voter_id: int = Query(..., description="ID of the voter")
):
    """Return the length of the cast ballot record (CBR) for a voter in an election.
    Args:
        election_id (int): Id of the election.
        voter_id (int): Id of the voter.
    Returns:
        Length of the CBR.
    """
    cbr_length = db.fetch_cbr_length(voter_id, election_id)

    return {"cbr_length": cbr_length}


@app.get("/cbr-for-voter")
def send_cbr_for_voter_in_election(
    election_id: int = Query(..., description="ID of the election"),
    voter_id: int = Query(..., description="ID of the voter")
):
    """Return the cast ballot record (CBR) for a voter in an election.
    Args:
        election_id (int): Id of the election.
        voter_id (int): Id of the voter.
    Returns:
        IndexImageCBR: Object containing CBR information.
    """
    voter_cbr: IndexImageCBR = db.fetch_cbr_for_voter_in_election(voter_id, election_id)
    return voter_cbr


@app.get("/fetch-ballot-hashes")
def fetch_ballot_hashes(
    election_id: int = Query(..., description="ID of the election")
):
    """Return all ballot hashes for a given election.
    Args:
        election_id (int): Id of the election.
    Returns:
        List of ballot hashes.
    """
    ballot_hashes = db.fetch_ballot_hashes(election_id)
    return {"ballot_hashes": ballot_hashes}


@app.get("/fetch_last_ballot_ctvs")
def fetch_last_ballot_ctvs(election_id):
    """Return all last ballot ciphertexts for candidate chioce (CTVs) for an election.
    Used for tallying. 
    Args:
        election_id: Id of the election.
    Returns:
        JSON representation of the last ballot ciphertexts.
    """
    last_ballot_ctvs_json = db.fetch_last_ballot_ctvs(election_id)

    return {"last_ballot_ctvs": last_ballot_ctvs_json}


@app.post("/receive-election-result")
def receive_election_result(election_result: ElectionResult):
    """Receive and store the final result for an election.
    Args:
        election_result (ElectionResult): Election result data to be stored.
    """
    print(f"{PURPLE}Received election result for {election_result.electionid}. Saving to database...")
    db.save_election_result(election_result)


@app.get("/election-result")
def send_election_result(
    election_id: int = Query(..., description="ID of the election")
):
    """Retrieve the stored election result for a given election.
    Args:
        election_id (int): Id of the election.
    Returns:
        ElectionResult: Stored result for the election.
    Raises:
        HTTPException: If no result exists for the given election.
    """
    election_result = db.fetch_election_result(election_id)
    if election_result is None:
        raise HTTPException(status_code=404, detail="Election result not Found")
    return election_result

@app.get("/ballot")
def get_ballot(
    election_id: int = Query(..., description="ID of the election"),
    voter_id: int = Query(..., description="ID of the voter"),
    image_filename: str = Query(..., description="Image filename associated with the ballot")
):
    ballot: Ballot = db.fetch_ballot(election_id, voter_id, image_filename)
    print(f"ballot fetched for image: {image_filename}:", ballot)
    return ballot

@app.get("/preceding-ballots")
def get_preceding_ballots(
    election_id: int = Query(..., description="ID of the election"),
    voter_id: int = Query(..., description="ID of the voter"),
    timestamp: str = Query(..., description="Timestamp associated with the ballot")
):
    last_ballot, previous_last_ballot = db.fetch_preceeding_ballots(voter_id, election_id, timestamp)

    return {"last_ballot": last_ballot, "previous_last_ballot": previous_last_ballot}