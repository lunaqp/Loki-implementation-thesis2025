# Ballot = (id, upk, ct_bar)
from keygen import g, order 

def generate_ballot0(voter_id, public_key_voter, candidates, public_key_TS, public_key_VS):
    ctbar_0 = build_ctbar0(candidates, public_key_TS, public_key_VS)
    ballot0 = (voter_id, public_key_voter, ctbar_0)
    print(f"Ballot 0: {ballot0}")
    return ballot0

def build_ctbar0(candidates, public_key_TS, public_key_VS):
    r0 = order.random()
    x = [0]*candidates
    ct0 = [enc(g, public_key_TS, x[j], r0) for j in range(candidates)]
    ctl0 = enc(g, public_key_VS, 0, r0)
    ctlid = ctl0 # ctlid is identical to ctlv for ballot 0 since it sets "ctl0 = ctlid = enc(pk_vs, 0, r)".
    return (ct0, ctl0, ctlid, r0)
             
# Encryption function
# Parameters: generator, public key to encrypt with, message to encrypt and randomness for encryption.
def enc(g, pk, m, r):
    c0 = r*g
    c1 = m*g + r*pk
    return (c0, c1)

# def send_ballot0_to_vs(ballot0):
