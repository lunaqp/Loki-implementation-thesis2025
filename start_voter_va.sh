#to create voter containers run in linux terminal: ./start_voter_va.sh 101
set -euo pipefail #safty check, exit if commands fail.

#if no argument/voterid is given the script stops
if [ $# -lt 1 ]; then
  echo "Usage: $0 <voter-id>"
  exit 1
fi

VOTER_ID="$1" #voterid is first commandline arg.

# Simple scheme to derive unique ports per voter
VA_API_PORT=$((9000 + VOTER_ID))   # e.g. voter 101 -> 9101
VA_WEB_PORT=$((10000 + VOTER_ID))  # e.g. voter 101 -> 10101

PROJECT_NAME="voter_${VOTER_ID}"

echo "Starting VA for voter ${VOTER_ID}"
echo "  API  on host port ${VA_API_PORT}"
echo "  WEB  on host port ${VA_WEB_PORT}"
echo "  compose project: ${PROJECT_NAME}"

VOTER_ID="${VOTER_ID}" \
VA_API_PORT="${VA_API_PORT}" \
VA_WEB_PORT="${VA_WEB_PORT}" \
docker compose \
  -p "${PROJECT_NAME}" \
  --profile va \
  up -d --build va_api va_web
