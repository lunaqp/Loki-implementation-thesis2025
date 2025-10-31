from fastapi import FastAPI, Query
import asyncio
from keygen import send_public_key_to_BB
from coloursTS import PURPLE
from tallying import tally

app = FastAPI()

# Triggered by RA when RA has created group, generator, and order.
@app.get("/ts_resp")
async def ts_resp():
    asyncio.create_task(send_public_key_to_BB()) # Calling send_public_key_to_BB implicitly fetches group, g, and order from BB, generates keys, and sends them to BB.
    return {"service": "TS", "result": "TS fetched g and order from db + created keymaterial and saved to db"}

@app.get("/health")
def health():
    return {"ok": True}

@app.post("/notify-election-over")
def notified_election_over(election_id: int = Query(..., description="ID of the election")):
    print(f"{PURPLE}Election over with ID: {election_id}. \nProceeding to tallying")
    tally(election_id)