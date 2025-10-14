import httpx

# Notify TallyingServer and VotingServer of g and order being saved to database.
async def notify_ts_vs_params_saved():
    print("Notifying Tallying and Voting server of Elgamal parameters saved to database") # NOTE: Add try/catch block.
    async with httpx.AsyncClient() as client:
        # Call TallyingServer:
        resp_TS = await client.get("http://ts_api:8000/ts_resp")
        # Call VotingServer:
        resp_VS = await client.get("http://vs_api:8000/vs_resp")

    return resp_TS.json(), resp_VS.json()