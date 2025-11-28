#!/usr/bin/env bash
set -e

# Starts SSH tunnels in background
ssh -o "StrictHostKeyChecking no" -N -L 8001:172.18.0.6:8000 pensim@130.226.143.130 & # BB
ssh -o "StrictHostKeyChecking no" -N -L 8002:172.18.0.7:8000 pensim@130.226.143.130 & # RA
ssh -o "StrictHostKeyChecking no" -N -L 8004:172.18.0.2:8000 pensim@130.226.143.130 & # VS

# Starts API server
exec uvicorn apiVA:app --host 0.0.0.0 --port 8000
