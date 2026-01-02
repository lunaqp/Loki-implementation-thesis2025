#!/usr/bin/env bash

set -e

GREEN="\033[0;32m"
YELLOW="\033[1;33m"
RED="\033[0;31m"
NC="\033[0m" # No Color

# Checking if db.env file exists and creating it if needed
ENV_DIR="./docker/env"
ENV_FILE="./docker/env/db.env"

if [[ ! -f "./docker/env/db.env" ]]; then
    echo -e "${YELLOW}db.env not found. Creating it...${NC}"

    # Create directory if it does not exist
    mkdir -p "./docker/env"

    # Create db.env file with required content
    cat > "./docker/env/db.env" <<'EOF'
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=appdb
POSTGRES_HOST=db
POSTGRES_PORT=5432
EOF
else
    echo -e "${GREEN}db.env already exists. Proceeding...${NC}"
fi

# Closing and removing docker images
echo -e "${GREEN}Closing and removing Docker images...${NC}"
docker compose down

# Removing data in docker volumes
echo -e "${GREEN}Removing Docker data volumes...${NC}"
docker volume rm backendsystems_vs_data || true
docker volume rm backendsystems_db_data || true
docker volume rm backendsystems_ra_data || true

# Building Docker images
echo -e "${GREEN}Building docker images...${NC}"
docker compose up --build -d

# Loop indefinitely until user chooses to exit
while true; do
    echo
    echo -e "${YELLOW}---------- Choose an option ----------${NC}"
    echo "1: Load election 1"
    echo "2: Load election 2"
    echo "3: Rerun application from scratch"
    echo "4: Exit (closes and removes Docker images)"

    read -rp "Enter your choice (1-4): " choice

    case "$choice" in
        1)
            echo -e "${GREEN}Loading election 1...${NC}"
            curl -X POST "http://localhost:8002/elections/load-file?name=election1.json"
            ;;
        2)
            echo -e "${GREEN}Loading election 2...${NC}"
            curl -X POST "http://localhost:8002/elections/load-file?name=election2.json"
            ;;
        3)
            echo -e "${GREEN}Rerun docker${NC}"
            docker compose down
            exec "$0"
            ;;
        4)
            echo -e "${GREEN}Exiting. Closing and removing Docker images...${NC}"
            docker compose down
            exit 0
            ;;
        *)
            echo -e "${RED}Invalid selection. Choose a number from 1-4${NC}"
            ;;
    esac
done
