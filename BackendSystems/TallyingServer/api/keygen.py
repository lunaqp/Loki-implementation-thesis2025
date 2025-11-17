import httpx
import base64
import os
import json
from coloursTS import BLUE
from fetchFunctions import fetch_elgamal_params

async def keygen():
    _, GENERATOR, ORDER = await fetch_elgamal_params()
    secret_key = ORDER.random() 
    public_key = secret_key * GENERATOR
    print(f"{BLUE}TS public and private key generated")
    
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    SECRET_KEY_PATH = os.path.join(BASE_DIR, 'keys.json')

    data = {"public_key": base64.b64encode(public_key.export()).decode(), "secret_key": base64.b64encode(secret_key.binary()).decode()}

    # Saving keys to json-file:
    with open(SECRET_KEY_PATH, 'w') as file:
        json.dump(data, file)
    print(f"{BLUE}Secret key saved to {SECRET_KEY_PATH}")

    
    return public_key

async def send_public_key_to_BB():
    public_key = await keygen()
    payload = {"service": "TS", "key": base64.b64encode(public_key.export()).decode()} # converting to byte-object and then applying base64 encoding for transferring

    async with httpx.AsyncClient() as client:
        response = await client.post("http://bb_api:8000/receive-public-key", json=payload)

    try:
        response_data = response.json() if response.content else None
    except ValueError:
        response_data = response.text

    return {"status": "sent TS public key to BB", "response": response_data}