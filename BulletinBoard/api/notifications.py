import httpx
from fastapi import HTTPException
from coloursBB import BLUE, RED

# Notify TallyingServer and VotingServer of g and order being saved to database.
async def notify_ts_vs_params_saved():
    print(f"{BLUE}Notifying Tallying and Voting server of Elgamal parameters saved to database") # NOTE: Add try/catch block.
    async with httpx.AsyncClient() as client:
        # Call TallyingServer:
        resp_TS = await client.get("http://ts_api:8000/ts_resp")
        # Call VotingServer:
        resp_VS = await client.get("http://vs_api:8000/vs_resp")

    return resp_TS.json(), resp_VS.json()

async def notify_ra_public_key_saved(service):
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.post("http://ra_api:8000/key_ready", json={
                "service": service,
                "status": "ok"})
            print(f"{BLUE}Notification sent to RA for {service} key:", resp.status_code, resp.text) # Should error handling be based on response code as well as exceptions?
        except Exception as e:
            raise HTTPException(status_code=502, detail=f"{RED}Unable to send keys to RA: {e}")