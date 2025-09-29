from fastapi import FastAPI
import os
from keygen import g, order
from zksk import Secret, DLRep

app = FastAPI()
DATABASE_URL = os.getenv("DATABASE_URL")

@app.get("/health")
def health():
    return{"ok": True}

print(f"g: {g}")
print(f"order: {order}")
one = Secret(value=1)
print(f"zksk one: {one}")