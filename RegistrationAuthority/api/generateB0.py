from keygen import GROUP, GENERATOR, ORDER 
import psycopg
from fetchNewElection import CONNECTION_INFO
from petlib.ec import EcPt

def generate_ballot0(voter_id, public_key_voter, candidates): # Ballot = (id, upk, ct_bar)
    ctbar_0 = build_ctbar0(candidates)
    ballot0 = (voter_id, public_key_voter, ctbar_0)
    return ballot0

def fetch_public_keys():
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
    print(f"pk_ts: {public_key_TS}")
    print(f"type of pk_ts: {type(public_key_TS)}")
    print(f"pk_vs: {public_key_VS}")
    print(f"type of pk_vs: {type(public_key_VS)}")
    cur.close()
    conn.close()
    return public_key_TS, public_key_VS

def build_ctbar0(candidates): # ctbar = (ctv, ctlv, ctlid, proof)
    public_key_TS, public_key_VS = fetch_public_keys()
    r0 = ORDER.random()
    x = [0]*candidates
    ct0 = [enc(GENERATOR, public_key_TS, x[j], r0) for j in range(candidates)]
    ctl0 = enc(GENERATOR, public_key_VS, 0, r0)
    ctlid = ctl0 # ctlid is identical to ctlv for ballot 0 since it sets "ctl0 = ctlid = enc(pk_vs, 0, r)".
    return (ct0, ctl0, ctlid, r0)
             
# Encryption function
# Parameters: generator, public key to encrypt with, message to encrypt and randomness for encryption.
def enc(g, pk, m, r):
    c0 = r*g
    c1 = m*g + r*pk
    return (c0, c1)

# def send_ballot0_to_vs(ballot0):
def send_ballotlist_to_votingserver(ballot_list):
    print("Sending ballot to vs...") # NOTE: Add actual functionality.