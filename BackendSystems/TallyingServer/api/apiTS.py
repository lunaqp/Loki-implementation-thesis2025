from fastapi import FastAPI
import asyncio
from keygen import send_public_key_to_BB
from tallying import handle_election

app = FastAPI()

# Triggered by RA when RA has created group, generator, and order.
@app.get("/ts_resp")
async def ts_resp():
    asyncio.create_task(send_public_key_to_BB()) # Calling send_public_key_to_BB implicitly fetches group, g, and order from BB, generates keys, and sends them to BB.
    return {"service": "TS", "result": "TS fetched g and order from db + created keymaterial and saved to db"}

@app.get("/health")
def health():
    return {"ok": True}

@app.post("/receive-election")
async def notified_election_received(payload: dict):
    election_id = payload.get("electionid")
    
    # Background tasks for handling each election
    asyncio.create_task(handle_election(election_id))

    return {"status": "received", "election_id": election_id}
