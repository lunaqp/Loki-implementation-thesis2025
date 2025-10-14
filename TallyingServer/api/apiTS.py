from fastapi import FastAPI, HTTPException
import os
import psycopg
import asyncio
from petlib.bn import Bn # For casting database values to petlib big integer types.
from petlib.ec import EcGroup, EcPt, EcGroup
import httpx

DATABASE_URL = os.getenv("DATABASE_URL")

DBNAME = os.getenv("POSTGRES_DB", "appdb")
DBUSER = os.getenv("POSTGRES_USER", "postgres")
DBPASSWORD = os.getenv("POSTGRES_PASSWORD", "postgres")
DBHOST = os.getenv("POSTGRES_HOST", "db")
DBPORT = os.getenv("POSTGRES_PORT", "5432")

CONNECTION_INFO = f"dbname={DBNAME} user={DBUSER} password={DBPASSWORD} host={DBHOST} port={DBPORT}"

app = FastAPI()

# Triggered by RA when RA has created group, generator, and order.
@app.get("/ts_resp")
async def ts_resp():
    asyncio.create_task(send_pk_to_DB()) # Calling send_pk_to_DB implicitly fetches group, g, and order from db and generates keys.
    return {"service": "TS", "result": "TS fetched g and order from db + created keymaterial and saved to db"}

@app.get("/health")
def health():
    return {"ok": True}

async def get_order():
    with psycopg.connect(CONNECTION_INFO) as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT GroupCurve, Generator, OrderP
                FROM GlobalInfo
                WHERE ID = 0
            """)
            row = cur.fetchone()
            (group, generator, order) = row
            # Convert database values to Petlib types:
            GROUP = EcGroup(group)
            GENERATOR = EcPt.from_binary(generator, GROUP)
            ORDER = Bn.from_binary(order)
            print(f"generator: {GENERATOR}")
            print(f"order: {ORDER}")
            print(f"group: {GROUP}")
            return GROUP, GENERATOR, ORDER
        cur.close()
        conn.close()

async def keygen():
    _, GENERATOR, ORDER = await get_order()
    secret_key = ORDER.random() 
    public_key = secret_key * GENERATOR
    print("TS public and private key generated")

    return secret_key, public_key

# async def send_publickey_to_bb(KEY):
#     _, public_key = await keygen() 
#     async with httpx.AsyncClient() as client:
#         try:
#             resp = await client.post("http://ra_api:8000/key_ready", json={
#                 "service": "TS",
#                 "status": "ok"})
#             print("Notification sent to RA:", resp.status_code, resp.text)
#         except Exception as e:
#             raise HTTPException(status_code=502, detail=f"Unable to send keys to RA: {e}")

async def send_pk_to_DB():
    _, public_key = await keygen() 
    with psycopg.connect(CONNECTION_INFO) as conn:
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE GlobalInfo
                SET PublicKeyTallyingServer = %s
                WHERE ID = 0
            """, (public_key.export(),))
        conn.commit()
        cur.close()
        conn.close()
    # NOTE: We need to store secret key somehow.

    # Notify Registration Authority of key creation:
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.post("http://ra_api:8000/key_ready", json={
                "service": "TS",
                "status": "ok"})
            print("Notification sent to RA:", resp.status_code, resp.text)
        except Exception as e:
            raise HTTPException(status_code=502, detail=f"Unable to send keys to RA: {e}")