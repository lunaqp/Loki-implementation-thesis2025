"""This file is used for notifying RA, TS, and VS.

It provides asynchronous helper functions used to notify external
services: Tallying Server (TS), Voting Server (VS), and
Registration Authority (RA), about important events in the setup phase.
"""
import httpx
from fastapi import HTTPException
from coloursBB import BLUE, RED

# Notify TallyingServer and VotingServer of g and order being saved to database.
async def notify_ts_vs_params_saved():
    """Notify the Tallying Server and Voting Server that Elgamal parameters are stored.
    This endpoint is used after the Registration Authority posts the ElGamal
    parameters on the BB/DB. Both TS and VS can then begin to generate their keys once the
    parameters become available.
    Returns:
        tuple: JSON responses from the Tallying Server and Voting Server.
    Raises:
        httpx.HTTPError: If an HTTP transport error occurs while contacting
        either.
    """
    print(f"{BLUE}Notifying Tallying and Voting server of Elgamal parameters saved to database") # NOTE: Add try/catch block.
    async with httpx.AsyncClient() as client:
        # Call TallyingServer:
        resp_TS = await client.get("http://ts_api:8000/ts_resp")
        # Call VotingServer:
        resp_VS = await client.get("http://vs_api:8000/vs_resp")

    return resp_TS.json(), resp_VS.json()

async def notify_ra_public_key_saved(service):
    """Notify the Registration Authority that a public key for a service is stored.
    This function informs the RA that a new public key (from VS or TS)
    has been saved in the bulletin board database.
    Args:
        service (str): The name of the service whose key was stored.
    Returns:
        None
    Raises:
        HTTPException: If the RA cannot be contacted/the request fails.
    """
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.post("http://ra_api:8000/key_ready", json={
                "service": service,
                "status": "ok"})
            print(f"{BLUE}Notification sent to RA for {service} key:", resp.status_code, resp.text) # Should error handling be based on response code as well as exceptions?
        except Exception as e:
            raise HTTPException(status_code=502, detail=f"{RED}Unable to send keys to RA: {e}")