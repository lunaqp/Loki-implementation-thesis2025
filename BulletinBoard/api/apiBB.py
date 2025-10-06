#Has to run along with other api's + web app. To run -> python apiBB.py
import queries as db
from fastapi import FastAPI
import os
import psycopg

app = FastAPI()
DATABASE_URL = os.getenv("DATABASE_URL")

# # Loading testdata into database (temporary)
# DBNAME = os.getenv("POSTGRES_DB", "appdb")
# DBUSER = os.getenv("POSTGRES_USER", "postgres")
# DBPASSWORD = os.getenv("POSTGRES_PASSWORD", "postgres")
# DBHOST = os.getenv("POSTGRES_HOST", "db")
# DBPORT = os.getenv("POSTGRES_PORT", "5432")

# # After having created a postgres database, establish connection with the relevant info:
# conn = psycopg.connect(dbname=DBNAME, user=DBUSER, password=DBPASSWORD, host=DBHOST, port=DBPORT)

# # Open a cursor to perform database operations
# cur = conn.cursor()

# cur.execute("SELECT COUNT(*) FROM Elections;")
# row_count = cur.fetchone()[0]

# if row_count == 0:
#     print("Database is empty, inserting test values...")
#     with open("testvalues.sql", "r") as f:
#         sql = f.read()
#     cur.execute(sql)
#     conn.commit()
# else:
#     print(f"Database already has data, skipping insertion.")

# cur.close()
# conn.close()

@app.get("/health")
def health():
    return{"ok": True}

@app.get("/hello") #Defines HTTP Get route at /hello
#a function that runs when client requests /hello
def hello():
    return {"message": "Hello World from BulletinBoard!"}

@app.get("/candidates")
def candidates():
    candidates = db.fetch_candidates_for_election(0)
    candidates_dict = [{"id": cid, "name": name} for cid, name in candidates]
    print(candidates_dict)
    return {"candidates": candidates_dict}

