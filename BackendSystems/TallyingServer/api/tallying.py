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
    print(f"{CYAN}Election with ID {election_id} loaded.")
    # Calculate time until election is over
    _, election_end = await fetch_electiondates_from_bb(election_id)
    tz = pytz.timezone('Europe/Copenhagen')

    remaining_time = election_end - datetime.now(tz)
    print(f"remaining time: {remaining_time}")

    # Wait until election is over
    await asyncio.sleep(remaining_time.total_seconds()) # Adding slight delay to ensure voting server wraps up last obfuscation ballot for each voter.
    grace_period = 5 # seconds
    print(f"{PURPLE}Election {election_id} has concluded, giving grace period of {grace_period} seconds before tallying begins")
    await asyncio.sleep(grace_period)

    # Tally the election result
    print(f"{PURPLE}Tallying election with id {election_id}...")
    s_time_tally = time.process_time_ns()
    election_result: ElectionResult = await tally(election_id)
    e_time_tally = time.process_time_ns() - s_time_tally
    print(f"{PINK}Tallying time:", e_time_tally/1000000, "ms")
    await send_result_to_bb(election_result)

# Tally function:
async def tally(election_id):
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

# Tally statement:
def stmt_tally(generator, order, votes, c0, c1, sk_TS):
    one=Secret(value=1)
    neg_c0 = (-1)*c0
    return DLRep(votes*generator, one*c1 + sk_TS*neg_c0)

def dec(ct, sk):
    c0, c1 = ct
    message = (c1 + (-sk*c0))

    return message

def convert_to_ecpt(ctv_list, GROUP):
    # Converting to binary
    ctv_bin = []
    for ctvs in ctv_list: # for each voter ctv-list
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
    
    # alternatively:
    # new_list = [[(EcPt.from_binary(base64.b64decode(ct0), GROUP),EcPt.from_binary(base64.b64decode(ct1), GROUP)) for ct0, ct1 in ctvs] for ctvs in ctv_list]

    return ctv_ecpt


async def send_result_to_bb(election_result: ElectionResult):
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post("http://bb_api:8000/receive-election-result", json=election_result.model_dump())
            response.raise_for_status() 

        return {"status": "ok"}
    except Exception as e:
        print(f"{RED}Error sending election result to Bulletin Board: {e}")
        return {"status": "Error sending election result to Bulletin Board", "error": str(e)}