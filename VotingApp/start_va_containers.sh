#to create voter containers run in linux terminal: ./start_voter_va.sh 101
set -euo pipefail #safty check, exit if commands fail.

#if no argument/voterid is given the script stops
if [ $# -lt 1 ]; then
  echo "Usage: $0 <voter-id>"
  exit 1
fi

VOTER_ID="$1" #voterid is first commandline arg.

PROJECT_NAME="voter_${VOTER_ID}"

echo "Starting VA for voter ${VOTER_ID}"
echo "  compose project: ${PROJECT_NAME}"

export VOTER_ID="$VOTER_ID"

docker compose \
  -p "${PROJECT_NAME}" \
  up -d --build va_api va_web
