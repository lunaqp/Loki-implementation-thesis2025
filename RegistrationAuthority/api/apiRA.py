from fastapi import FastAPI
import os

app = FastAPI()
DATABASE_URL = os.getenv("DATABASE_URL")

@app.get("/health")
def health():
    return{"ok": True}