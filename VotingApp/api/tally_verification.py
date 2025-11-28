from zksk import Secret, base, DLRep
import fetch_functions_va as ff
from modelsVA import ElectionResult
import base64
from petlib.ec import EcPt

async def verify_tally(election_id):
    try:
        GROUP, GENERATOR, ORDER = await ff.fetch_elgamal_params()
        election_result: ElectionResult = await ff.fetch_election_result_from_bb(election_id)
        candidates = len(election_result.result) # The result list has one entry per candidate  
        voters = len(await ff.fetch_voters_from_bb(election_id))
        last_ballots_ctvs_b64 = await ff.fetch_last_ballot_ctvs_from_bb(election_id)
        last_ballots_ctvs = convert_to_ecpt(last_ballots_ctvs_b64, GROUP)

        stmt=[]
        for i in range(candidates):
            votes = election_result.result[i].votes

            c0, c1 =(0*GENERATOR), (0*GENERATOR)
            for j in range(voters):
                c0+=last_ballots_ctvs[j][i][0]
                c1+=last_ballots_ctvs[j][i][1]
            print(f"votes: {votes} \n c0: {c0} \n c1: {c1} \n secret:  {Secret()}")
            stmt.append(stmt_tally(GENERATOR, ORDER, votes, c0, c1, Secret()))

        for i in range(candidates):
            proof = deserialise(election_result.result[i].proof)
            verified = stmt[i].verify(proof)
            print(f"Verification for tallying of votes for candidate {i+1}: {verified}")
            if not verified:
                return False 
            
        return True
    except Exception as e:
        print(f"Error during verification: {e}")
        return False


# Tally statement:
def stmt_tally(generator, order, votes, c0, c1, sk_TS):
    one=Secret(value=1)
    neg_c0 = (-1)*c0
    return DLRep(votes*generator, one*c1 + sk_TS*neg_c0)

def dec(ct, sk):
    c0, c1 = ct
    message = (c1 + (-sk*c0))

    return message

def deserialise(proof):
      proof_bin = base64.b64decode(proof)
      proof = base.NIZK.deserialize(proof_bin)

      return proof


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

    return ctv_ecpt