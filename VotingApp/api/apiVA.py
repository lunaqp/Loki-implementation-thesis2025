#To run -> npm run api
from fastapi import FastAPI
import os
from bulletin_routes import router as bulletin_router
import base64

app = FastAPI()
DATABASE_URL = os.getenv("DATABASE_URL")

@app.get("/health")
def health():
    return{"ok": True}

# Register FastAPI router
app.include_router(bulletin_router)

@app.get("/api/election")
def get_election_id():
    return {"electionId": 123}

@app.post("/receive-secret-key")
def receive_secret_key(data: dict):
    voter_id = data["voter_id"]
    election_id = data["election_id"]
    enc_secret_key = data["secret_key"]
    print(f"voterid: {voter_id}, electionid: {election_id}, secretkey: {enc_secret_key}")
    print(f"secret key decoded: {base64.b64decode(enc_secret_key)}")

    # TODO: Figure out where to save secret keys/how to store.
    return {"status": "secret key received"}