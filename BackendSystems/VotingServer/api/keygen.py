import httpx
import base64
import os
import json
from coloursVS import BLUE
from fetch_functions import fetch_elgamal_params

async def keygen():
    """
    Generate ElGamal key pair, store them locally in 'keys.json',
    and return the generated public key.
    """
    # Fetch ElGamal parameters (GROUP, GENERATOR, ORDER)
    _, GENERATOR, ORDER = await fetch_elgamal_params()

    # Generate secret key as a random element in ORDER and compute public key
    secret_key = ORDER.random() 
    public_key = secret_key * GENERATOR

    print(f"{BLUE}VS public and private key generated")

    # Build path to keys.json in the project directory
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    SECRET_KEY_PATH = os.path.join(BASE_DIR, 'keys.json')

    # Convert key data to base64 for safe transmission
    data = {"public_key": base64.b64encode(public_key.export()).decode(), "secret_key": base64.b64encode(secret_key.binary()).decode()}

    # Save generated keys to json-file
    with open(SECRET_KEY_PATH, 'w') as file:
        json.dump(data, file)

    print(f"{BLUE}Secret key saved to {SECRET_KEY_PATH}")

    return public_key

async def send_public_key_to_BB():
    """
    Generate a new key pair and send the public key to the Bulletin Board (BB) API.
    Returns status + server response.
    """
    # Generate keys and get public key
    public_key = await keygen()

    # Convert key data to base64 for safe transmission
    payload = {"service": "VS", "key": base64.b64encode(public_key.export()).decode()} # converting to byte-object and then applying base64 encoding for transferring

    # Send POST request containing public key to BB
    async with httpx.AsyncClient() as client:
        response = await client.post("http://bb_api:8000/receive-public-key", json=payload)
    
    # Attempt to parse the JSON response
    try:
        response_data = response.json() if response.content else None
    except ValueError:
        response_data = response.text

    return {"status": "sent VS public key to BB", "response": response_data}