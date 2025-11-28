from modelsVA import Ballot
from zksk import Secret, base
from petlib.ec import EcPt
from statement import stmt
import base64
import time
from coloursVA import GREEN, ORANGE, BOLD, PINK
import fetch_functions_va as ff

async def verify_proof(election_id, voter_id, pyballot: Ballot):
    GROUP, GENERATOR, _, _, candidates, pk_TS, pk_VS = await fetch_data(election_id, voter_id)

    current_ballot_b64 = (pyballot.ctv, pyballot.ctlv, pyballot.ctlid, pyballot.proof)
    ctv_current, ctlv_current, ctlid_current, proof_current = convert_to_ecpt(current_ballot_b64, GROUP)
    
    # Fetch the two ballots preceding the provided ballot:
    last_ballot_b64, previous_last_ballot_b64 = await ff.fetch_preceding_ballots_from_bb(election_id, voter_id, pyballot.timestamp)
    
    last_ballot = convert_to_ecpt(last_ballot_b64, GROUP)
    previous_last_ballot = convert_to_ecpt(previous_last_ballot_b64, GROUP)

    upk = EcPt.from_binary(base64.b64decode(pyballot.upk), GROUP) # Recreating voter public key as EcPt object
    s_time_verify = time.process_time_ns() # Performance testing: Start timer for ballot

    ctv = last_ballot[0]
    ctlv = last_ballot[1]
    ctlid = last_ballot[2]

    ct_i = (2 * ctlid[0], 2 * ctlid[1])
    c0, c1 = ctlv[0] - ctlid[0], ctlv[1] - ctlid[1]
    
    # last previous ballot from voter's CBR if it exists, otherwise the last ballot is also the last previous ballot
    ctv2 = previous_last_ballot[0]

    stmt_c = stmt((GENERATOR, pk_TS, pk_VS, upk, ctv_current, ctlv_current, ctlid_current, ct_i, c0, c1, ctv, ctv2), 
                (Secret(), Secret(), Secret(), Secret(), Secret(), Secret()), len(candidates))
    
    statement_verified = stmt_c.verify(proof_current)

    e_time_verify = time.process_time_ns() - s_time_verify
    print(f"{PINK}Ballot verification time:", e_time_verify/1000000, "ms")

    if not statement_verified: 
        print(f"{ORANGE}verification failed")
        #NOTE: if failed to verify send message to voting app and display in UI "ballot not valid"
    else:
        print(f"{BOLD}{GREEN}Ballot succesfully verified")

    return stmt_c.verify(proof_current)


def convert_to_ecpt(ballot, GROUP):
    ct_v_b64, ct_lv_b64, ct_lid_b64, proof_b64 = ballot
    # Convert base64 encodings so all four elements are in binary
    ct_v_bin = [(base64.b64decode(x), base64.b64decode(y)) for (x, y) in ct_v_b64]
    ct_lv_bin = tuple(base64.b64decode(x) for x in ct_lv_b64)
    ct_lid_bin = tuple(base64.b64decode(x) for x in ct_lid_b64)
    proof_bin = base64.b64decode(proof_b64)
    
    # convert from binary into EcPt objects and a NIZK proof object.
    ct_v = [(EcPt.from_binary(x, GROUP), EcPt.from_binary(y, GROUP)) for (x, y) in ct_v_bin]
    ct_lv = (EcPt.from_binary(ct_lv_bin[0], GROUP), EcPt.from_binary(ct_lv_bin[1], GROUP))
    ct_lid = (EcPt.from_binary(ct_lid_bin[0], GROUP), EcPt.from_binary(ct_lid_bin[1], GROUP))
    if len(proof_b64) < 100: # suboptimal solution to avoid attempts at deserialising ballot0.
        proof = proof_bin
    else:
        proof = base.NIZK.deserialize(proof_bin)

    return (ct_v, ct_lv, ct_lid, proof)


async def fetch_data(election_id, voter_id):
    GROUP, GENERATOR, ORDER = await ff.fetch_elgamal_params()
    cbr_length = await ff.fetch_cbr_length_from_bb(voter_id, election_id)
    candidates: list = await ff.fetch_candidates_from_bb(election_id)
    pk_TS, pk_VS = await ff.fetch_public_keys_from_bb()

    return GROUP, GENERATOR, ORDER, cbr_length, candidates, pk_TS, pk_VS