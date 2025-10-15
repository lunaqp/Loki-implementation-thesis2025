import psycopg
import os

DB_NAME = os.getenv("POSTGRES_DB", "appdb")
DB_USER = os.getenv("POSTGRES_USER", "postgres")
DB_PASS = os.getenv("POSTGRES_PASSWORD", "postgres")
DB_HOST = os.getenv("POSTGRES_HOST", "db")  # docker service name
DB_PORT = int(os.getenv("POSTGRES_PORT", "5432"))
CONNECTION_INFO = f"dbname={DB_NAME} user={DB_USER} password={DB_PASS} host={DB_HOST} port={DB_PORT}" # all info that psycopg needs to connect to db

## ---------------- WRITING TO DB ---------------- ##

def save_elgamalparams(GROUP, GENERATOR, ORDER):
    print("saving Elgamal parameters to database")
    conn = psycopg.connect(CONNECTION_INFO)
    cur = conn.cursor()
    cur.execute("""
                UPDATE GlobalInfo
                SET GroupCurve = %s, Generator = %s, OrderP = %s
                WHERE ID = 0
                """, (GROUP, GENERATOR, ORDER))
    conn.commit()
    cur.close()
    conn.close()

def save_key_to_db(service, KEY):
    if service == "TS":
        column = "PublicKeyTallyingServer"
    elif service == "VS":
        column = "PublicKeyVotingServer"
        
    conn = psycopg.connect(CONNECTION_INFO)
    cur = conn.cursor()
    cur.execute(f"""
        UPDATE GlobalInfo
        SET {column} = %s
        WHERE ID = 0
        """, (KEY,))
    conn.commit()
    cur.close()
    conn.close()
    print(f"public key received from {service} and saved to database")


## ---------------- READING FROM DB ---------------- ##


async def fetch_params():
    with psycopg.connect(CONNECTION_INFO) as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT GroupCurve, Generator, OrderP
                FROM GlobalInfo
                WHERE ID = 0
            """)
            (GROUP, GENERATOR, ORDER) = cur.fetchone()
            return GROUP, GENERATOR, ORDER
        cur.close()
        conn.close()