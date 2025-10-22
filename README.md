# Loki-implementation-thesis2025

A prototype implementation the coercion-resistant e-voting scheme Loki as proposed in "Thwarting Last-Minute Voter Coercion" by Rosario Giustolisi, Maryam Sheikhi Garjan, and Carsten Schuermann.

This project has been created using Python version XX and Node version 22.

How to run the app:
To run app:
docker compose up -d --build

To close app/containers:
docker compose down

Load new election file without FastApi: docker exec -it loki-implementation-thesis2025-ra_api-1 python /app/fetchNewElection.py /app/data/election1.json

Call/load new election file with FastApi: "Invoke-RestMethod -Uri "http://localhost:8002/elections/load-file?name=election1.json" -Method Post" in terminal

Remove data from db: docker volume rm loki-implementation-thesis2025_db_data
