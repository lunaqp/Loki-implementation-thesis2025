from fastapi import FastAPI
import os
import psycopg
import asyncio

app = FastAPI()

DATABASE_URL = os.getenv("DATABASE_URL")

DBNAME = os.getenv("POSTGRES_DB", "appdb")
DBUSER = os.getenv("POSTGRES_USER", "postgres")
DBPASSWORD = os.getenv("POSTGRES_PASSWORD", "postgres")
DBHOST = os.getenv("POSTGRES_HOST", "db")
DBPORT = os.getenv("POSTGRES_PORT", "5432")

CONNECTION_INFO = f"dbname={DBNAME} user={DBUSER} password={DBPASSWORD} host={DBHOST} port={DBPORT}"

# Event from RegistrationAuthority to signal that keys can be generated.
#ready_for_keygen_event = asyncio.Event()

@app.get("/vs_resp")
async def vs_resp():
    asyncio.create_task(get_order())
    return {"service": "VS", "result": "Processed by VS"}

async def get_order():
    with psycopg.connect(CONNECTION_INFO) as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT Generator, OrderP
                FROM GlobalInfo
                WHERE ID = 0
            """)
            row = cur.fetchone()
            (Generator, OrderP) = row
            print(f"generator: {Generator}")
            print(f"order: {OrderP}")
            return Generator, OrderP
        cur.close()
        conn.close()

# async def keygen():
#     Generator, OrderP = await get_order()

#     secret_key = OrderP.random() 
#     print(f"secret key type: {type(secret_key)}") # type = petlib.bn.Bn
#     public_key = secret_key * Generator
#     print(f"pk: {public_key}")
#     print(f"sk: {secret_key}")

#     return secret_key, public_key

# async def send_pk_to_DB():
#     _, public_key = await keygen()

#     with psycopg.connect(CONNECTION_INFO) as conn:
#         with conn.cursor() as cur:
#             cur.execute("""
#                 UPDATE GlobalInfo
#                 SET PublicKeyVotingServer = %s
#                 WHERE ID = 0
#             """), (str(public_key))
#         cur.close()
#         conn.close()