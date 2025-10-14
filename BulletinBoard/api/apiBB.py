#Has to run along with other api's + web app. To run -> python apiBB.py
import queries as db
from fastapi import FastAPI
import os
import psycopg
from models import ElGamalParams
import base64
import dbcalls as db
from notifications import notify_ts_vs_params_saved
import asyncio

app = FastAPI()

@app.get("/health")
def health():
    return{"ok": True}

@app.get("/hello") #Defines HTTP Get route at /hello
#a function that runs when client requests /hello
def hello():
    return {"message": "Hello World from BulletinBoard!"}

# @app.get("/candidates")
# def candidates():
#     candidates = db.fetch_candidates_for_election(0)
#     candidates_dict = [{"id": cid, "name": name} for cid, name in candidates]
#     print(candidates_dict)
#     return {"candidates": candidates_dict}

@app.get("/elgamalparams")
async def get_params():
    GROUP, GENERATOR, ORDER = await db.fetch_params()

    return {
    "group": GROUP,
    "generator": base64.b64encode(GENERATOR).decode(), # Base 64 encoded for tranfer
    "order": base64.b64encode(ORDER).decode(),  # Base 64 encoded for tranfer
    }



@app.post("/receive-params")
async def receive_params(params: ElGamalParams):
    GROUP = params.group
    GENERATOR = base64.b64decode(params.generator)
    ORDER = base64.b64decode(params.order)

    # Creating an async loop for the database access since psycopg2 only allows syncronized access.
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, db.save_elgamalparams, GROUP, GENERATOR, ORDER)
    await notify_ts_vs_params_saved()

    return {"status": "ElGamal parameters saved"}

@app.post("/vs-key")
def receive_key(key):
    KEY = base64.b64decode(key)
    db.save_key_to_db("VS", KEY)

    return {"status": "Voting Server public key saved"}

@app.post("/ts-key")
def receive_key(key):
    db.save_key_to_db("TS", key)

    return {"status": "Tallying Server public key saved"}
