import os
from fastapi import FastAPI, HTTPException, Query
import json
from fetchNewElection import DATA_DIR, NewElectionData, load_election_into_db
from keygen import save_globalinfo_to_db, keygen, save_keys_to_db
from generateB0 import generate_ballot0

app = FastAPI()

@app.get("/health")
def health():
    return {"ok": True}

# Read the new election from the json file. using fastapi
# POST endpoint, reads filename from query string ex. name=election1.json
@app.post("/elections/load-file")
def load_election_from_file(name: str = Query(..., description="Filename inside DATA_DIR")):
    
    path = os.path.join(DATA_DIR, name) #builds path in DATA_DIR
    if not os.path.isfile(path):
        raise HTTPException(status_code=404, detail=f"File not found: {path}")
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f) #reads and parses json file

        payload = NewElectionData.model_validate(data) #pyladic validation, converts raw dict into typed NewElectionData
        load_election_into_db(payload) #calls loader to write into the DB, returns small succes msg
        
        # Generate and save voter keys to database
        voter_id_list = [voter.id for voter in payload.voters ]
        election_id = payload.election.id
        voter_info = keygen(voter_id_list, election_id)
        save_keys_to_db(voter_info)

        # Generate ballot0 for each voter
        voter_id_upk = [(b, c) for (_, b, c, _) in voter_info]
        ballot0_list = []
        for voter_id, public_key_voter in voter_id_upk:
            print(f"id = {voter_id}, upk = {public_key_voter}")
            #ballot0 = generate_ballot0(voter_id, public_key_voter, payload.candidates, 2, 2) # Tallying Server and VotingServer keys temporarily edited.
        #     ballot0_list.append(ballot0)
        # for item in ballot0_list:
        #     print(f"item: {item}")    

        return {"status": "loaded", "election_id": payload.election.id, "file": name}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

save_globalinfo_to_db()
