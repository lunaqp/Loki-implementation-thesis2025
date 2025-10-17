from models import Ballot
import os
import psycopg
from zksk import Secret
from petlib.bn import Bn # For casting database values to petlib big integer types.
from petlib.ec import EcGroup, EcPt, EcGroup
import hashlib
from statement import stmt


DB_NAME = os.getenv("POSTGRES_DB", "appdb")
DB_USER = os.getenv("POSTGRES_USER", "postgres")
DB_PASS = os.getenv("POSTGRES_PASSWORD", "postgres")
DB_HOST = os.getenv("POSTGRES_HOST", "db")  # docker service name
DB_PORT = int(os.getenv("POSTGRES_PORT", "5432"))
CONNECTION_INFO = f"dbname={DB_NAME} user={DB_USER} password={DB_PASS} host={DB_HOST} port={DB_PORT}"

conn = psycopg.connect(CONNECTION_INFO)

cur = conn.cursor()

def fetch_voters_for_election(election_id):
    cur.execute("""
                SELECT ID
                FROM Voters v
                Join VoterParticipatesInElection ve on v.ID = ve.VoterID
                WHERE ve.ElectionID = %s;"""
                ,(election_id,))
    voter_list = cur.fetchall()
    return voter_list

def fetch_candidates_for_election(election_id):
    cur.execute("""
                SELECT CandidateID
                FROM CandidateRunsInElection c
                WHERE ElectionID = %s;"""
                ,(election_id,))
    candidate_list = cur.fetchall()
    return candidate_list

def fetch_public_keys(GROUP):
    conn = psycopg.connect(CONNECTION_INFO)
    cur = conn.cursor()
    cur.execute("""
                SELECT PublicKeyTallyingServer, PublicKeyVotingServer
                FROM GlobalInfo
                WHERE ID = 0
                """)
    public_key_ts_bin, public_key_vs_bin = cur.fetchone()
    public_key_TS = EcPt.from_binary(public_key_ts_bin, GROUP)
    public_key_VS = EcPt.from_binary(public_key_vs_bin, GROUP)
    cur.close()
    conn.close()

    return public_key_TS, public_key_VS


def fetch_upk(GROUP, voter_id, election_id):
    conn = psycopg.connect(CONNECTION_INFO)
    cur = conn.cursor()
    cur.execute("""
                SELECT PublicKey
                FROM VoterParticipatesInElection
                WHERE VoterID = %s AND ElectionID = %s;
                """, voter_id, election_id)
    upk = cur.fetchone()
    upk = EcPt.from_binary(upk, GROUP)
    cur.close()
    conn.close()

    return upk

def fetch_ballot_hash(election_id):
    cur.execute("""
                SELECT BallotHash
                FROM Ballots
                Join VoterCastsBallot vcb on vcb.BallotID = Ballots.ID
                WHERE vcb.ElectionID = %s;"""
                ,(election_id,))
    ballot_hash = cur.fetchall()
    return ballot_hash 

# Fetches the CBR for a given voter in a given election sorted by most recent votes at the top.
def fetch_CBR_for_voter_in_election(voter_id, election_id): # We currently also gets the voters public and private keys. Do we want to move this to the Voter table?
    cur.execute("""
                SELECT *
                FROM VoterParticipatesInElection p
                JOIN VoterCastsBallot c 
                ON p.ElectionID = c.ElectionID AND p.VoterID = c.VoterID
                JOIN Ballots b
                ON b.ID = c.BallotID
                WHERE p.ElectionID = %s AND p.VoterID = %s
                ORDER BY c.VoteTimestamp DESC;
                """, (election_id, voter_id))
    cbr = cur.fetchall()
    return cbr

def fetch_last_and_previouslast_ballot(voter_id, election_id): # We currently also gets the voters public and private keys. Do we want to move this to the Voter table?
    cur.execute("""
                SELECT *
                FROM VoterParticipatesInElection p
                JOIN VoterCastsBallot c 
                ON p.ElectionID = c.ElectionID AND p.VoterID = c.VoterID
                JOIN Ballots b
                ON b.ID = c.BallotID
                WHERE p.ElectionID = %s AND p.VoterID = %s
                ORDER BY c.VoteTimestamp DESC
                LIMIT 2;
                """, (election_id, voter_id))
    cbr = cur.fetchall()
    return cbr

async def get_order():
    with psycopg.connect(CONNECTION_INFO) as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT GroupCurve, Generator, OrderP
                FROM GlobalInfo
                WHERE ID = 0
            """)
            row = cur.fetchone()
            (group, generator, order) = row
            # Convert database values to Petlib types:
            GROUP = EcGroup(group)
            GENERATOR = EcPt.from_binary(generator, GROUP)
            ORDER = Bn.from_binary(order)
            print(f"generator: {GENERATOR}")
            print(f"order: {ORDER}")
            print(f"group: {GROUP}")
            return GROUP, GENERATOR, ORDER
        cur.close()
        conn.close()

cbr = fetch_CBR_for_voter_in_election(election_id=543, voter_id=109)
voter_list = fetch_voters_for_election(election_id = "789")

def validateBallot(Ballot, election_id):
    ballot_hash = fetch_ballot_hash(election_id) #NOTE Do we need compare the hash of the new ballot with all ballot hashes in an election or only the ballot hashes for that voter id. ot whole BB

    hashed_ballot = hashlib.sha256(Ballot.model_dump_json().encode("utf-8")).hexdigest() #hash the ballot
    print(hashed_ballot)

    uid_exists = False
    ballot_not_included = False
    proof_verified = False

    for id in voter_list:
        if Ballot.id == id:
            uid_exists = True

    for hash in ballot_hash:
        if hashed_ballot == hash:
            ballot_not_included = True

    proof_verified = verify_proof(election_id, Ballot.id)

    ballot_validated = uid_exists and ballot_not_included and proof_verified

    return ballot_validated

    #NOTE Function to create the hash value in RA missing.


def verify_proof(election_id, voter_id):

    #for idx, cbr in enumerate(CBR[i][1:], start=1):  
    last_ballot, previous_last_ballot = fetch_last_and_previouslast_ballot(election_id, voter_id)
    _, GENERATOR, GROUP = get_order()
    candidates = fetch_candidates_for_election(election_id)
    pk_T, pk_vs = fetch_public_keys(GROUP)
    upk = fetch_upk(GROUP, voter_id, election_id)

    ctv = last_ballot[1]
    ctlv = last_ballot[2]
    ctlid = last_ballot[3]
    proof = last_ballot[4]

    ct_i = (2 * ctlid[0], 2 * ctlid[1])
    c0, c1 = ctlv[0] - ctlid[0], ctlv[1] - ctlid[1]
    
    # last previous ballot from voter's CBR if it exists, otherwise the last ballot is also the last previous ballot
    ctv2 = previous_last_ballot[1]
    #NOTE: What if DB only has 1 element/ballot

    stmt_c = stmt((GENERATOR, pk_T, pk_vs, upk, cbr[0], cbr[1], cbr[2], ct_i, c0, c1, ctv, ctv2), 
                (Secret(), Secret(), Secret(), Secret(), Secret(), Secret()), candidates)

    if not stmt_c.verify(proof): 
        print("verification failed")
        #NOTE: if failed to verify send messaeg to voting app and display in UI "ballot not valid"
    else:
        print("\nVerification successful ballot")

    return stmt_c.verify(proof)


# Function for re-encryption
# Parameters: generator, public key, ciphertext, randomness
def re_enc(g, pk, ct, r):
    
    c0, c1 = ct

    c0Prime = c0 + r*g
    c1Prime = c1 + r*pk

    return (c0Prime, c1Prime)

# Function for decryption
# Parameters: ciphertext & secret key.
def dec(ct, sk):
    c0, c1 = ct

    message = (c1 + (-sk*c0))

    return message

#NOTE: We recieve a ballot  with a uid, then we can get the cbr for that id, we are missing this
#NOTE we are missing the time aspect of potentially calling obfuscate many times asynchronously maybe??
    
def obfuscate(GENERATOR, ORDER, sk_vs, upk, pk_T, pk_vs, candidates, cbr):
    #Generate a noise ballot
    r_v = Secret(value=ORDER.random())
    r_lv = Secret(value=ORDER.random())
    r_lid = Secret(value=ORDER.random())
    sk = Secret(value=sk_vs)

    last_ballot = cbr[-1]

    if len(cbr)<2:
       #if there is no last previous ballot then we use the last ballot as the previous ballot
       previous_last_ballot=last_ballot
    else: previous_last_ballot=cbr[-2]

    ct_bar_lv, ct_bar_lid = last_ballot[1], last_ballot[2]

    ct_i=(2*ct_bar_lid[0],2*ct_bar_lid[1])  
    ct_lv=re_enc(GENERATOR, pk_vs, ct_i, r_lv.value) 
    ct_lid=re_enc(GENERATOR, pk_vs, ct_i, r_lid.value) 

    c0 = ct_bar_lv[0]-ct_bar_lid[0]
    c1 = ct_bar_lv[1]-ct_bar_lid[1]
    ct = (c0, c1)
    g_m_dec = dec(ct, sk.value)

    if g_m_dec==0*GENERATOR:
    #if 1 = Dec(sk_vs, (ct_lv-1)-(ct_lid-1)) then we re-randomize the last ballot 
        ct_bar_v=last_ballot[0]
        sim_relation=2
        print(f"[{len(cbr)}] VS obfuscated last ballot")
    else : 
        ct_bar_v=previous_last_ballot[0]
        sim_relation=1
        print(f"\033[31m[{len(cbr)}] VS obfuscated previous last ballot\033[0m")
    
    ct_v = [re_enc(GENERATOR, pk_T, ct_bar_v[i], r_v.value) for i in range(candidates)]

    full_stmt=stmt((GENERATOR, pk_T, pk_vs, upk, ct_v, ct_lv, ct_lid, ct_i, c0, c1, last_ballot[0], previous_last_ballot[0]),(r_v, Secret(), r_lv, r_lid, Secret(), sk), candidates )
    full_stmt.subproofs[0].set_simulated()
    
    #depending on whether 1 = Dec(sk_vs, (ct_lv-1)-(ct_lid-1)) or not we simulate R2 or R3, other than R1
    full_stmt.subproofs[sim_relation].set_simulated()
    nizk = full_stmt.prove({r_v: r_v.value, r_lv: r_lv.value, r_lid: r_lid.value, sk: sk.value})

    return (ct_v, ct_lv, ct_lid, nizk)


