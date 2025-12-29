"""Tally verification functions for the Voting App.

This module verifies that the posted election tally is consistent with the
published ciphertexts, using the NIZK proofs included in the BB's election
result.

1) Fetch ElGamal parameters and the final election result from BB.
2) Fetch the last ciphertext vote (ctv) for each voter from BB.
3) Recompute per-candidate aggregated ciphertexts.
4) Reconstruct the ZK statement for each candidate tally.
5) Deserialize the proof and verify it against the statement.

This verification does not recompute votes; it checks the cryptographic proof
  that the posted vote count matches the aggregated ciphertexts.
"""

from zksk import Secret, base, DLRep
import fetch_functions_va as ff
from modelsVA import ElectionResult
import base64
from petlib.ec import EcPt

async def verify_tally(election_id):
    """Verify tally correctness for a given election id.

    Args:
        election_id: Election identifier.

    Returns:
     bool: ``True`` if all per-candidate tally proofs verify; otherwise ``False``.
    """
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

def deserialise(proof):
      """Deserialize a base64-encoded NIZK proof.

    Args:
        proof: Base64-encoded serialized proof.

    Returns:
        object: Deserialized proof object.
    """
      proof_bin = base64.b64decode(proof)
      proof = base.NIZK.deserialize(proof_bin)

      return proof


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