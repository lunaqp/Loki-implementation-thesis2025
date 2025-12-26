"""Election tallying logic for TS.

This module:
1) Wait until election end time (plus a configurable grace period).
2) Fetch final encrypted vote ciphertexts from BB.
3) Decrypt ciphertexts for each candidate using the TS secret key.
4) Determine vote counts by matching decrypted group elements.
5) Generate a discrete-log representation proof (zksk DLRep) for each candidate.
6) Post results + proofs to BB.
"""

from zksk import Secret, base, DLRep
from petlib.ec import EcPt
import httpx
from coloursTS import RED, PURPLE, CYAN, PINK
import base64
from modelsTS import CandidateResult, ElectionResult
import pytz
from datetime import datetime
import asyncio
from fetchFunctions import fetch_candidates_from_bb, fetch_voters_from_bb, fetch_last_ballot_ctvs_from_bb, fetch_ts_secret_key, fetch_electiondates_from_bb, fetch_elgamal_params
import time

async def handle_election(election_id):
    """Waits for an election to finish, then tally and publish the result.
    Calculate time until election is over and waits.
    Adds a delay to ensure voting server wraps up last obfuscation ballot for each voter. Amount of time necessary depends on election setup.
    This function is expected to be scheduled as a background task.
    
    Args:
        election_id: Election identifier.
    """
    print(f"{CYAN}Election with ID {election_id} loaded.")
    _, election_end = await fetch_electiondates_from_bb(election_id)
    tz = pytz.timezone('Europe/Copenhagen')

    remaining_time = election_end - datetime.now(tz)
    print(f"remaining time: {remaining_time}")

    await asyncio.sleep(remaining_time.total_seconds())
    
    grace_period = 60 # seconds
    print(f"{PURPLE}Election {election_id} has concluded, giving grace period of {grace_period} seconds before tallying begins")
    await asyncio.sleep(grace_period) 

    # Tally
    print(f"{PURPLE}Tallying election with id {election_id}...")
    election_result: ElectionResult = await tally(election_id)
    await send_result_to_bb(election_result)

async def tally(election_id):
    """Tally the election and constructs all candidate proofs for Tally
    
    Args:
        election_id: Election identifier.
 
    Returns:
        ElectionResult: Pydantic election result including vote totals and proofs.
    """
    GROUP, GENERATOR, ORDER = await fetch_elgamal_params()
    candidates = await fetch_candidates_from_bb(election_id)
    candidates_length = len(candidates)
    voters_length = len(await fetch_voters_from_bb(election_id))
    sk_TS = fetch_ts_secret_key()
    last_ballots_ctvs_b64: list = await fetch_last_ballot_ctvs_from_bb(election_id)
    last_ballots_ctvs = convert_to_ecpt(last_ballots_ctvs_b64, GROUP)
    sk=Secret(value=sk_TS)
    stmt, nizk=[], []
    votes_for_candidate=[0]*candidates_length
    
    for i in range(candidates_length):
        c0, c1 = (0*GENERATOR), (0*GENERATOR)

        #summing up all encrypted votes for a candidate
        for j in range(voters_length):
            c0+= last_ballots_ctvs[j][i][0]
            c1+= last_ballots_ctvs[j][i][1]
        sum_votes=dec((c0,c1), sk_TS)

        #finding the number of votes for a candidate
        for j in range(voters_length):
            if sum_votes==j*GENERATOR:
                votes_for_candidate[i]=j
                break

        print(f"{PURPLE}Votes for Candidate", candidates[i],":", votes_for_candidate[i])
        
        #constructing the statement for the ZK proof
        stmt.append(stmt_tally(GENERATOR, ORDER, j, c0, c1, sk))

        #proving the statement
        nizk.append(stmt[-1].prove({sk: sk.value}))

    print(f"{PURPLE}Abstention votes:", voters_length-sum(votes_for_candidate)) 

    # serialising and base64 encoding NIZK proof:
    proofs_bin = [base.NIZK.serialize(c_proof) for c_proof in nizk]
    proofs_b64 = [base64.b64encode(c_proof_bin).decode() for c_proof_bin in proofs_bin]

    # Creating a list of pydantic objects matching each candidate id with the associated result.
    candidate_results = [CandidateResult(candidateid = cid, votes = v, proof = p) for cid, v, p in zip(candidates, votes_for_candidate, proofs_b64)]

    # Create the ElectionResult model containing both the votes for each candidate and the tallying proof.
    election_result: ElectionResult = ElectionResult(
        electionid = election_id,
        result = candidate_results,
    )

    return election_result

def stmt_tally(generator, order, votes, c0, c1, sk_TS):
    """Construct a statement for the ZK proofs in Tally.

    Args:
        generator: EC generator.
        votes: Claimed vote count for the candidate (as an integer).
        c0, c1: Aggregated ciphertext components.
        sk_ts: TS secret key.

    Returns:
        tuple: A zksk discrete-log representation statement for tally.
    """
    one=Secret(value=1)
    neg_c0 = (-1)*c0
    return DLRep(votes*generator, one*c1 + sk_TS*neg_c0)

def dec(ct, sk):
    """Decrypt an ElGamal ciphertext under secret key ``sk``.

    Args:
        ct: Ciphertext tuple ``(c0, c1)``.
        sk: Secret key.

    Returns:
        EcPt: Decrypted element corresponding to the plaintext.
    """
    c0, c1 = ct
    message = (c1 + (-sk*c0))

    return message

def convert_to_ecpt(ctv_list, GROUP):
    """Convert a base64 ciphertext list to EC points.

    Args:
        ctv_list: Ciphertext structure as base64 strings:
        ``[ [ [ct0_b64, ct1_b64], ... per candidate ], ... per voter ]``.
        group: Petlib group used to decode points.

    Returns:
        list[list[tuple[EcPt, EcPt]]]: Ciphertexts converted to ``EcPt`` pairs.
    """
    # Converting to binary
    ctv_bin = []
    for ctvs in ctv_list: # for each voter
        decoded_pairs = []
        for ct0, ct1 in ctvs: # for the ciphertext pairs for each candidate
            decoded_pairs.append((base64.b64decode(ct0), base64.b64decode(ct1)))
        ctv_bin.append(decoded_pairs)

    # Converting to ecpt
    ctv_ecpt = []
    for ctvs in ctv_bin: # for each voter ctv-list
        decoded_pairs = []
        for ct0, ct1 in ctvs: # for the ciphertext pairs for each candidate
            decoded_pairs.append((EcPt.from_binary(ct0, GROUP), EcPt.from_binary(ct1, GROUP)))
        ctv_ecpt.append(decoded_pairs)
    
    return ctv_ecpt


async def send_result_to_bb(election_result: ElectionResult):
    """Send the final election result (and proofs) to BB.

    Args:
        election_result: Computed election result.

    Returns:
        dict[str, str]: Status payload.
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post("http://bb_api:8000/receive-election-result", json=election_result.model_dump())
            response.raise_for_status() 

        return {"status": "ok"}
    except Exception as e:
        print(f"{RED}Error sending election result to Bulletin Board: {e}")
        return {"status": "Error sending election result to Bulletin Board", "error": str(e)}