"""
Ballot validation and obfuscation utilities for the Voting Server (VS).
This module implements cryptographic verification and obfuscation of ballots
using ElGamal encryption and non-interactive zero-knowledge (NIZK) proofs.
It is responsible for:

- Validating ballots against election state and Bulletin Board (BB) data.
- Verifying cryptographic proofs of correct construction of ballots.
- Obfuscating ballots via re-encryption and proof simulation.
- Constructing serialized ballot objects for transmission.
- Fetching cryptographic parameters, keys, and election metadata.

The module integrates with petlib and zksk for elliptic-curve cryptography
and zero-knowledge proofs, and communicates with the Bulletin Board to
retrieve election state.
"""
from modelsVS import Ballot
import os
from zksk import Secret, base
from petlib.bn import Bn # For casting database values to petlib big integer types.
from petlib.ec import EcPt
from statement import stmt
import base64
from hashVS import hash_ballot
import json
from coloursVS import GREEN, ORANGE, YELLOW, PINK, BOLD
import fetchFunctions as ff
import time

e_time_obf = [] # Performance timing for ballot obfuscation without network calls.

async def validate_ballot(pyballot:Ballot):
    """
    Validate a ballot submitted by a voter.

    Validation includes:
    - Checking that the voter is eligble to participate in the election
    - Ensuring the ballot is not already included on the Bulletin Board.
    - Verifying the NIZK proof verifying the correct construction of the ballot.

    Args:
        pyballot (Ballot): Ballot to validate.

    Returns:
        bool: True if the ballot is valid, otherwise False.
    """
    election_id = pyballot.electionid
    ballot_hash: list = await ff.fetch_ballot_hash_from_bb(election_id) # Fetch list of all ballot-hashes from BB.
    voter_list: list = await ff.fetch_voters_from_bb(election_id)

    hashed_ballot = hash_ballot(pyballot) # Generate hash for current voter-cast ballot.  
    uid_exists = False
    ballot_not_included = False
    proof_verified = False

    # Check that voter is included in list of eligible voters.
    for id in voter_list:
        if pyballot.voterid == id:
            uid_exists = True

    # Check that ballot hash of curret ballot is not already included in the Bulletin Board.
    if not ballot_hash: # Guarding against empty list, not necessary if we dont have to validate Ballot0
        ballot_not_included = True
    if hashed_ballot not in ballot_hash:
        ballot_not_included = True

    # Verify proof
    proof_verified = await verify_proof(election_id, pyballot.voterid, pyballot)

    # Ballot is validated if 1) voter is eligible to participate 2) ballot does not exist on BB and 3) proof can be verified.
    ballot_validated = uid_exists and ballot_not_included and proof_verified

    return ballot_validated

async def verify_proof(election_id, voter_id, pyballot):
    """
    Verify the zero-knowledge proof of correct construction of the ballot.

    Args:
        election_id: Identifier of the election.
        voter_id: Identifier of the voter.
        pyballot (Ballot): pydantic Ballot containing ciphertexts and proof.

    Returns:
        bool: True if the proof verifies successfully, otherwise False.
    """
    GROUP, GENERATOR, _, cbr_length, candidates, pk_TS, pk_VS = await fetch_data(election_id, voter_id)
    current_ballot_b64 = (pyballot.ctv, pyballot.ctlv, pyballot.ctlid, pyballot.proof)
    ctv_current, ctlv_current, ctlid_current, proof_current = convert_to_ecpt(current_ballot_b64, GROUP)
    
    # Fetch last ballot and previous last ballot from Bulletin Board if there is at least two ballots on the Bulletin Board.
    if cbr_length >= 2:
        last_ballot_b64, previous_last_ballot_b64 = await ff.fetch_last_and_previouslast_ballot_from_bb(election_id, voter_id)
    else:
        # if there is no previous last ballot then we use the last ballot as the previous last ballot
        last_ballot_b64, _ = await ff.fetch_last_and_previouslast_ballot_from_bb(election_id, voter_id)
        previous_last_ballot_b64 = last_ballot_b64

    # Convert ballots back into petlib objects
    last_ballot = convert_to_ecpt(last_ballot_b64, GROUP)
    previous_last_ballot = convert_to_ecpt(previous_last_ballot_b64, GROUP)

    upk = EcPt.from_binary(base64.b64decode(pyballot.upk), GROUP) # Recreating voter public key as EcPt object

    ctv = last_ballot[0]
    ctlv = last_ballot[1]
    ctlid = last_ballot[2]

    # Setting integer representation of CBR index (ct_i) and comparing voter provided list of previous ballots to the correct list of previous ballots.
    ct_i = (2 * ctlid[0], 2 * ctlid[1])
    c0, c1 = ctlv[0] - ctlid[0], ctlv[1] - ctlid[1]
    
    # last previous ballot from voter's CBR if it exists, otherwise the last ballot is also the last previous ballot
    ctv2 = previous_last_ballot[0]

    stmt_c = stmt((GENERATOR, pk_TS, pk_VS, upk, ctv_current, ctlv_current, ctlid_current, ct_i, c0, c1, ctv, ctv2), 
                (Secret(), Secret(), Secret(), Secret(), Secret(), Secret()), len(candidates))

    statement_verified = stmt_c.verify(proof_current)

    if not statement_verified: 
        print(f"{ORANGE}Verification failed")
    else:
        print(f"{BOLD}{GREEN}Ballot succesfully verified for voter {voter_id}")

    return statement_verified

def convert_to_ecpt(ballot, GROUP):
    """
    Convert base64-encoded ballot components into elliptic curve objects.

    Ciphertexts are reconstructed as EcPt objects, and the proof is either
    deserialized as a NIZK proof or returned as raw bytes for ballot0.

    Args:
        ballot (tuple): Base64-encoded ballot components.
        GROUP (EcGroup): Elliptic curve group.

    Returns:
        tuple: (ct_v, ct_lv, ct_lid, proof) in petlib-compatible form.
    """
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

def re_enc(g, pk, ct, r):
    """Re-Encryption of a ciphertext

    Args:
        g (EcPt): group generator
        pk (EcPt): public key of the receiver
        ct (EcPt, EcPt): ciphertext of encrypted message (c0, c1),
                         where c0 = r*g and c1 = m*g + r*pk
        r (Bn): randomness
    
    Returns:
        (c0Prime, c1Prime) (EcPt, EcPt): ciphertext (c0Prime, c1Prime)
                                         of re-encrypted ciphertext (c0, c1),
                                         where c0 = r*g and c1 = m*g + r*pk and,
                                         c0Prime = c0 + r*g and c1Prime = c1 + r*pk
    """
    c0, c1 = ct
    c0Prime = c0 + r*g
    c1Prime = c1 + r*pk

    return (c0Prime, c1Prime)

def dec(ct, sk):
    """Decryption of a ciphertext

    Args:
        ct (EcPt, EcPt): ciphertext of encrypted message (c0, c1),
                        where c0 = r*g and c1 = m*g + r*pk
        sk (Bn): secret key / decryption key
    
    Returns:
        message (EcPt): decrypted message, m, on the form m*g
    """
    c0, c1 = ct
    message = (c1 + (-sk*c0))

    return message

  
async def obfuscate(voter_id, election_id):
    """
    Cast an obfuscation ballot that is either a re-encryption of the last
    ballot or previous last ballot on the voter's Cast Ballot Record (CBR).
    
    If the previous ballot on the CBR was voter-cast with an incorrect list
    of indices identifying previously cast ballots (lv-list), then this
    ballot is skipped an the obfuscation ballot re-encrypts the ballot before
    it, the "previous last" ballot.
    
    This function:
    - Selects the appropriate previous ballot for obfuscation
    - Generates a NIZK proof demonstrating correctness
    - Returns a new obfuscated ballot

    Args:
        voter_id: Identifier of the voter.
        election_id: Identifier of the election.

    Returns:
        Ballot: Obfuscated ballot ready for submission.
    """
    GROUP, GENERATOR, ORDER, cbr_length, candidates, pk_TS, pk_VS = await fetch_data(election_id, voter_id)
    voter_public_key_bin = await ff.fetch_voter_public_key_from_bb(voter_id, election_id)
    upk = EcPt.from_binary(voter_public_key_bin, GROUP)     # Recreating voter public key as petlib EcPt object.

    # Fetch VS secret key from json file keys.json
    sk_VS = fetch_vs_secret_key()

    # Fetch last ballot and previous last ballot
    if cbr_length >= 2:
        last_ballot_b64, previous_last_ballot_b64 = await ff.fetch_last_and_previouslast_ballot_from_bb(election_id, voter_id)
    else:
        # if there is no last previous ballot then we use the last ballot as the previous last ballot
        last_ballot_b64, _ = await ff.fetch_last_and_previouslast_ballot_from_bb(election_id, voter_id)
        previous_last_ballot_b64 = last_ballot_b64

    last_ballot = convert_to_ecpt(last_ballot_b64, GROUP)
    previous_last_ballot = convert_to_ecpt(previous_last_ballot_b64, GROUP)
    s_time_obf = time.process_time_ns() # Performance: Start timer before obfuscation

    # Generate a noise ballot
    r_v = Secret(value=ORDER.random())
    r_lv = Secret(value=ORDER.random())
    r_lid = Secret(value=ORDER.random())
    sk = Secret(value=sk_VS)

    # fetching ct_lv and ct_lid from last_ballot to use for obfuscation.
    ct_lv, ct_lid = last_ballot[1], last_ballot[2]

    # Setting integer representation of CBR index (ct_i) and comparing voter provided list of previous ballots to the correct list of previous ballots.
    ct_i=(2*ct_lid[0],2*ct_lid[1])  
    
    # ct_lv and ct_lid are re-encrypted for the new obfuscated ballot.
    ct_lv_new=re_enc(GENERATOR, pk_VS, ct_i, r_lv.value) 
    ct_lid_new=re_enc(GENERATOR, pk_VS, ct_i, r_lid.value) 

    # If both ct_lv and ct_lid are encryptions of the same list, subtracting lid from lv will result in the equivalent of 0 (represented as 0*generator)
    c0 = ct_lv[0]-ct_lid[0]
    c1 = ct_lv[1]-ct_lid[1]
    ct = (c0, c1)
    g_m_dec = dec(ct, sk.value)

    # Obfuscating depending on comparison of lv and lid. If the result is 0 (represented as 0*generator), the lists are equivalent.
    if g_m_dec==0*GENERATOR:
    # If 1 = Dec(sk_vs, (ct_lv-1)-(ct_lid-1)) then we re-randomize the last ballot 
        ct_v=last_ballot[0]
        sim_relation=2 
        print(f"{YELLOW}[{cbr_length}] VS obfuscated last ballot for voter {voter_id}")
    else: 
        ct_v=previous_last_ballot[0]
        sim_relation=1
        print(f"{YELLOW}[{cbr_length}] VS obfuscated previous last ballot for voter {voter_id}")
    
    ct_v_new = [re_enc(GENERATOR, pk_TS, ct_v[i], r_v.value) for i in range(len(candidates))]

    full_stmt=stmt((GENERATOR, pk_TS, pk_VS, upk, ct_v_new, ct_lv_new, ct_lid_new, ct_i, c0, c1, last_ballot[0], previous_last_ballot[0]),(r_v, Secret(), r_lv, r_lid, Secret(), sk), len(candidates))
    full_stmt.subproofs[0].set_simulated()
    
    #depending on whether 1 = Dec(sk_vs, (ct_lv-1)-(ct_lid-1)) or not we simulate R2 or R3, other than R1
    full_stmt.subproofs[sim_relation].set_simulated()
    nizk = full_stmt.prove({r_v: r_v.value, r_lv: r_lv.value, r_lid: r_lid.value, sk: sk.value})

    e_time_obf.append(time.process_time_ns() - s_time_obf) # Performance: Append time taken to the timer array after obfuscation
    # print("e_time_obf:", e_time_obf)
    print(f"{PINK}Ballot obfuscation time (avg):", round(sum(e_time_obf)/len(e_time_obf)/1000000,3), "ms")
    
    pyBallot: Ballot = construct_ballot(voter_id, upk, ct_v_new, ct_lv_new, ct_lid_new, nizk, election_id)
    return pyBallot


def construct_ballot(voter_id, public_key, ct_v, ct_lv, ct_lid, proof, election_id):
    """
    Construct a serializable Ballot object from cryptographic components.

    All elliptic curve points and proofs are serialized and base64-encoded.

    Args:
        voter_id: Identifier of the voter.
        public_key (EcPt): Voter public key.
        ct_v (list): Vote ciphertexts.
        ct_lv (tuple): Ciphertext for voter-provided list of previous voter-cast ballots indices.
        ct_lid (tuple): Ciphertext for correct list of previous voter-cast ballots indices.
        proof: Zero-knowledge proof of correct construction of the ballot.
        election_id: Identifier of the election.

    Returns:
        Ballot: Serialized ballot object.
    """
    # Exporting bytes object for public key and encoding with base64
    public_key_b64 = base64.b64encode(public_key.export()).decode()

    # Encoding ciphertexts as base64.
    ct_v_b64 = [[base64.b64encode(x.export()).decode(), base64.b64encode(y.export()).decode()] for (x, y) in ct_v]
    ct_lv_b64 = [base64.b64encode(ct_lv[0].export()).decode(), base64.b64encode(ct_lv[1].export()).decode()]
    ct_lid_b64 = [base64.b64encode(ct_lid[0].export()).decode(), base64.b64encode(ct_lid[1].export()).decode()]
    
    # serialising and base64 encoding NIZK proof:
    proof_ser = base.NIZK.serialize(proof)
    proof_b64 = base64.b64encode(proof_ser).decode()

    pyBallot = Ballot(
            voterid = voter_id,
            upk = public_key_b64,
            ctv = ct_v_b64,
            ctlv = ct_lv_b64,
            ctlid = ct_lid_b64,
            proof = proof_b64,
            electionid = election_id
        )
    return pyBallot

def fetch_vs_secret_key():   
    """
    Load the Voting Server (VS) secret key from local storage.

    The secret key is read from a JSON file and reconstructed
    as a petlib big number.

    Returns:
        Bn: Voting Server secret key.
    """ 
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    SECRET_KEY_PATH = os.path.join(BASE_DIR, 'keys.json')

    with open(SECRET_KEY_PATH, 'r') as file:
        data = json.load(file)
    
    sk_VS = Bn.from_binary(base64.b64decode(data["secret_key"]))

    return sk_VS

async def fetch_data(election_id, voter_id):
    """
    Fetch all cryptographic and election-related data required for
    ballot validation or obfuscation.

    Args:
        election_id: Identifier of the election.
        voter_id: Identifier of the voter.

    Returns:
        tuple: (GROUP, GENERATOR, ORDER, cbr_length, candidates, pk_TS, pk_VS)
    """
    GROUP, GENERATOR, ORDER = await ff.fetch_elgamal_params()
    cbr_length = await ff.fetch_cbr_length_from_bb(voter_id, election_id)
    candidates: list = await ff.fetch_candidates_from_bb(election_id)
    pk_TS, pk_VS = await ff.fetch_public_keys_from_bb()

    return GROUP, GENERATOR, ORDER, cbr_length, candidates, pk_TS, pk_VS