from keygen import GROUP, GENERATOR, ORDER 
import psycopg
from fetchNewElection import CONNECTION_INFO
from petlib.ec import EcPt
from models import Ballot

def generate_ballot0(voter_id, public_key_voter, candidates): 
    # Build ctbar (ctbar = (ctv, ctlv, ctlid, proof))
    public_key_TS, public_key_VS = fetch_public_keys()
    r0 = ORDER.random()
    x = [0]*candidates
    ct0 = [enc(GENERATOR, public_key_TS, x[j], r0) for j in range(candidates)]
    ctl0 = enc(GENERATOR, public_key_VS, 0, r0)
    ctlid = ctl0 # ctlid is identical to ctlv for ballot 0 since it sets "ctl0 = ctlid = enc(pk_vs, 0, r)".
    # Build ballot (Ballot = (id, upk, ct_bar))
    ballot0 = (voter_id, public_key_voter, ct0, ctl0, ctlid, r0)

    return ballot0

# Fetch public keys from Tallying Server and Voting Server
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
    cur.close()
    conn.close()

    return public_key_TS, public_key_VS
             
# Encryption function
# Parameters: generator, public key to encrypt with, message to encrypt and randomness for encryption.
def enc(g, pk, m, r):
    c0 = r*g
    c1 = m*g + r*pk
    
    return (c0, c1)

# Serialising ballot 0 list into pydantic objects for transferring to VS
def serialise(ballot_list):
    serialised_ballot_list = []
    for ballot in ballot_list:
        id = ballot[0]
        upk = str(ballot[1])
        ctv = [[str(x), str(y)] for (x, y) in ballot[2]]
        ctlv = [str(ballot[3][0]), str(ballot[3][1])]
        ctlid = [str(ballot[4][0]), str(ballot[4][1])]
        proof = str(ballot[5])

        pyBallot = Ballot(
            id = id,
            upk = upk,
            ctv = ctv,
            ctlv = ctlv,
            ctlid = ctlid,
            proof = proof
        )
        serialised_ballot_list.append(pyBallot) 

    return serialised_ballot_list
    