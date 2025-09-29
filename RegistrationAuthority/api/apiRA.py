from fastapi import FastAPI
import os
from keygen import save_globalinfo_to_db, keygen, save_keys_to_db

app = FastAPI()

@app.get("/health")
def health():
    return{"ok": True}

save_globalinfo_to_db()

# Temporary for testing purposes.
voter_list = {
  "voters": [
    { "id": 0, "name": "Emma" },
    { "id": 1, "name": "Thomas" },
    { "id": 2, "name": "James" },
    { "id": 3, "name": "Karen" }
  ]
}

voterinfo = keygen(voter_list, 0)
save_keys_to_db(voterinfo)