import os
from fastapi import FastAPI, HTTPException, Query
import json
from fetchNewElection import (DATA_DIR, NewElectionData, load_election_into_db)
from keygen import save_globalinfo_to_db, keygen, save_keys_to_db, notify_ts_and_vs
import psycopg
import httpx
from contextlib import asynccontextmanager

# Defining startup functionality before the application starts:
@asynccontextmanager
async def lifespan(app: FastAPI):
    save_globalinfo_to_db()
    # Notify TallyingServer and VotingServer that g and order has been generated to trigger their own keygeneration.
    resp_TS, resp_VS = await notify_ts_and_vs()
    yield # yielding control back to FastApi

app = FastAPI(lifespan=lifespan)

# @app.get("/triggerkeygen")
# async def triggerkeygen():
#     resp_TS, resp_VS = await notify_ts_and_vs()
#     return {
#         "db_update": "success",
#         "tallying_server": resp_TS,
#         "voting_server": resp_VS
#     }
        

#app = FastAPI()

@app.get("/health")
def health():
    return {"ok": True}

# save_globalinfo_to_db()

# @app.get("/triggerkeygen")
# async def triggerkeygen():
    
#     # Notify TallyingServer and VotingServer that g and order has been generated to trigger their own keygeneration.
#     resp_TS, resp_VS = await notify_ts_and_vs()

#     return {
#         "db_update": "success",
#         "tallying_server": resp_TS,
#         "voting_server": resp_VS
#     }

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

        return {"status": "loaded", "election_id": payload.election.id, "file": name}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


