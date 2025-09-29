import os
from fastapi import FastAPI, HTTPException, Query
import json
from fetchNewElection import (DATA_DIR, NewElectionData, load_election_into_db,)

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
        return {"status": "loaded", "election_id": payload.election.id, "file": name}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
