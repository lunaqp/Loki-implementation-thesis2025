from fastapi import FastAPI
import os
import psycopg

# is not running because everything is running at the same time and apiRA has not yet posted order to DB when we try to get it here. 

app = FastAPI()

@app.get("/ts_resp")
async def ts_resp():
    return {"service": "TS", "result": "Processed by TS"}

DATABASE_URL = os.getenv("DATABASE_URL")

DBNAME = os.getenv("POSTGRES_DB", "appdb")
DBUSER = os.getenv("POSTGRES_USER", "postgres")
DBPASSWORD = os.getenv("POSTGRES_PASSWORD", "postgres")
DBHOST = os.getenv("POSTGRES_HOST", "db")
DBPORT = os.getenv("POSTGRES_PORT", "5432")

CONNECTION_INFO = f"dbname={DBNAME} user={DBUSER} password={DBPASSWORD} host={DBHOST} port={DBPORT}"

@app.get("/health")
def health():
    return {"ok": True}

def get_order():
    with psycopg.connect(CONNECTION_INFO) as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT Generator, OrderP
                FROM GlobalInfo
                WHERE ID = 0
            """)
            row = cur.fetchone()
            cur.close()
            conn.close()
            (Generator, OrderP) = row
            return Generator, OrderP

#Generator, OrderP = get_order()


def keygen():
    secret_key = OrderP.random() 
    print(f"secret key type: {type(secret_key)}") # type = petlib.bn.Bn
    public_key = secret_key * Generator
    print(f"pk: {public_key}")
    print(f"sk: {secret_key}")

    return secret_key, public_key

def send_pk_to_DB():
    with psycopg.connect(CONNECTION_INFO) as conn:
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE GlobalInfo
                SET PublicKeyTallier = %s
                WHERE ID = 0
            """), (str(public_key))

        conn.commit()
        cur.close()
        conn.close()

#secret_key, public_key = keygen()