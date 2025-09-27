#To run -> npm run api
from fastapi import FastAPI
import os
from bulletin_routes import router as bulletin_router

app = FastAPI()
DATABASE_URL = os.getenv("DATABASE_URL")

@app.get("/health")
def health():
    return{"ok": True}

# Register FastAPI router
app.include_router(bulletin_router)

@app.get("/api/election")
def get_election_id():
    return {"electionId": 123}