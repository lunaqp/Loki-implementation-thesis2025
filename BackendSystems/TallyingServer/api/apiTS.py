"""Tallying Server FastAPI Service/entrypoint.
This module uses ``asyncio.create_task`` to avoid blocking request handling.

This module includes:
- A readiness trigger endpoint (called by RA) that generates TS key material
  and publishes the Tallying Server public key to the Bulletin Board.
- An election notification endpoint that schedules when tallying for an election will start.
"""

from fastapi import FastAPI
import asyncio
from keygen import send_public_key_to_BB
from tallying import handle_election

app = FastAPI()

@app.get("/ts_resp")
async def ts_resp():
    """Initialize TS key material and publish the public key to BB.
    Triggered by RA after RA has created/published the ElGamal group parameters.
    Calling send_public_key_to_BB implicitly fetches group, g, and order from BB, generates keys, and sends them to BB
    
    Returns:
        dict[str, str]: Status payload indicating TS has begun key generation/publication.
    """
    asyncio.create_task(send_public_key_to_BB()) 
    return {"service": "TS", "result": "TS fetched g and order from db + created keymaterial and saved to db"}

@app.get("/health")
def health():
    """Healthcheck endpoint.

    Returns status of service running.
    """
    return {"ok": True}

@app.post("/receive-election")
async def notified_election_received(payload: dict):
    """Receive election notification and schedule tallying.

    Args:
        payload: Expected to include an electionid.

    Returns:
        dict[str, object]: Acknowledgement containing the received election id.
    """
    election_id = payload.get("electionid")
    
    # Background tasks for handling each election
    asyncio.create_task(handle_election(election_id))

    return {"status": "received", "election_id": election_id}
