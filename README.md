# Loki-implementation-thesis2025

A prototype implementation the coercion-resistant e-voting scheme Loki as proposed in "Thwarting Last-Minute Voter Coercion" by Rosario Giustolisi, Maryam Sheikhi Garjan, and Carsten Schuermann.

This project has been created using Python version 3.11 and Node version 20.

How to run the app:
To run app:
docker compose up -d --build

To close app/containers:
docker compose down

Load new election file without FastApi: docker exec -it loki-implementation-thesis2025-ra_api-1 python /app/fetchNewElection.py /app/data/election1.json

Call/load new election file with FastApi: "Invoke-RestMethod -Uri "http://localhost:8002/elections/load-file?name=election1.json" -Method Post" in terminal

Remove data from db: docker volume rm loki-implementation-thesis2025_db_data

# Use script to run project

To run script:
.\rundocker.ps1

This will run the script causing it to:

- First remove the docker images
- Delete from the database
- Then build the docker images again

From here you will then be given different options from 1-6:
1: Load election 1
2: Load election 2
3: Extract DuckDB file for Voting Server (timestamp table)
4: Extract DuckDB file for Voting App (voter keys)
5: Rerun application from scratch
6: Exit (closes and removes Docker images)
Choose by typing the number in the terminal.

while the docker images are build you can go to:
http://localhost:5173/ to see the frontend.

# Hosting the app

# Colour coding

We have colour-coded the log for all of the services based on the following:

- Blue: setup functionality running before any elections are received.
- Cyan: initialisation process once election is loaded
- Yellow: obfuscated ballots
- Green: all other ballots
- Purple: end of election and tallying
- Red: errors
