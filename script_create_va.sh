#!/bin/bash

echo -n "Enter voter ID: "
read VOTER_ID

if [ -z "$VOTER_ID" ]; then
  echo "Error: voter ID cannot be empty."
  exit 1
fi

API_CONTAINER="va_api_$VOTER_ID"
WEB_CONTAINER="va_web_$VOTER_ID"
VOLUME_NAME="va_duckdb_$VOTER_ID"

API_IMAGE="loki-implementation-thesis2025-va_api:latest"
WEB_IMAGE="loki-implementation-thesis2025-va_web:latest"

NETWORK="loki-implementation-thesis2025_default"

# Check if containers already exist
if docker ps -a --format '{{.Names}}' | grep -q "^$API_CONTAINER$"; then
  echo "Instance for voter $VOTER_ID already exists."
  exit 0
fi

# Create per-voter volume if missing
docker volume inspect "$VOLUME_NAME" >/dev/null 2>&1 || \
  docker volume create "$VOLUME_NAME"

echo "Starting API container $API_CONTAINER ..."
docker run -d \
  --name "$API_CONTAINER" \
  --network "$NETWORK" \
  -e BB_API_URL="http://bb_api:8000" \
  -e VOTER_SK_DECRYPTION_KEY="Al43dQKlM/aAjb5zBNYXBQ==" \
  -e DUCKDB_PATH="/duckdb/voter-keys.duckdb" \
  -e VOTER_ID="$VOTER_ID" \
  -v "$VOLUME_NAME:/duckdb" \
  "$API_IMAGE"

# echo "Starting WEB container $WEB_CONTAINER ..."
# docker run -d \
#   --name "$WEB_CONTAINER" \
#   --network "$NETWORK" \
#   -e VITE_API_VOTINGAPP="http://$API_CONTAINER:8000" \
#   "$WEB_IMAGE"

# Below creates the container without 
docker run --rm -it \
  --name "$WEB_CONTAINER" \
  --network "$NETWORK" \
  -e VITE_API_VOTINGAPP="http://$API_CONTAINER:8000" \
  "$WEB_IMAGE" \
  sh

echo "Instance created:"
echo "  API: $API_CONTAINER"
echo "  WEB: $WEB_CONTAINER"
