from fastapi import FastAPI
import asyncio
from keygen import send_public_key_to_BB
from models import BallotPayload
from validateBallot import validate_ballot, fetch_voter_public_key_from_bb
from epochGeneration import generate_timestamps

app = FastAPI()

@app.get("/health")
def health():
    return {"ok": True}

# Triggered by BB when BB has saved group, generator, and order to the database.
@app.get("/vs_resp")
async def vs_resp():
    asyncio.create_task(send_public_key_to_BB()) # Calling send_public_key_to_BB implicitly fetches group, g, and order from BB, generates keys, and sends them to BB.
    return {"service": "VS", "result": "VS fetched g and order from BB + created keymaterial and saved to BB"}

@app.post("/ballot0list")
async def receive_ballotlist(payload: BallotPayload):
    print(f"Received election {payload.electionid}, {len(payload.ballot0list)} ballots")

    for ballot in payload.ballot0list:
        if await validate_ballot(ballot, payload.electionid):
            print("ballot validated")
        else:
            print("ballot not valid")

    # NOTE: Validate ballots before sending to CBR via BB.

    await generate_timestamps(payload.electionid)
    return {"status": "ok"}
