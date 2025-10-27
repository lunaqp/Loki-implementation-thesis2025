from typing import Optional
from modelsVS import ElGamalParams
import httpx
import base64
from petlib.bn import Bn # For casting database values to petlib big integer types.
from petlib.ec import EcGroup, EcPt, EcGroup
from fastapi import HTTPException

# TODO: Find a good place to store params to avoid excessive database calls.
async def get_elgamal_params():
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get("http://bb_api:8000/elgamalparams")
            data = resp.json()
            params = ElGamalParams(
                group = data["group"],
                generator = data["generator"],
                order = data["order"]
            )

            # Convert to proper types for cryptographic functions.
            GROUP = EcGroup(params.group)
            GENERATOR = EcPt.from_binary(base64.b64decode(params.generator), GROUP)
            ORDER = Bn.from_binary(base64.b64decode(params.order))
            
            print(f"elgamal params fetched from BB: {GROUP}, \n {GENERATOR} \n {ORDER}")
            return GROUP, GENERATOR, ORDER
        
        except Exception as e:
            raise HTTPException(status_code=502, detail=f"Unable to fetch elgamal params: {e}") #NOTE: What would be the most correct status_codes for different scenarios?

async def keygen():
    _, GENERATOR, ORDER = await get_elgamal_params()
    secret_key = ORDER.random() 
    public_key = secret_key * GENERATOR
    print("VS public and private key generated")
    #TODO: save secret key somewhere locally
    return public_key

async def send_public_key_to_BB():
    public_key = await keygen()
    payload = {"service": "VS", "key": base64.b64encode(public_key.export()).decode()} # converting to byte-object and then applying base64 encoding for transferring

    async with httpx.AsyncClient() as client:
        response = await client.post("http://bb_api:8000/receive-public-key", json=payload)

    try:
        response_data = response.json() if response.content else None
    except ValueError:
        response_data = response.text

    return {"status": "sent VS public key to BB", "response": response_data}