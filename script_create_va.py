import docker
from docker.errors import NotFound

def create_va_instance(voter_id):
    client = docker.from_env()

    # Container names
    api_container_name = f"va_api_{voter_id}"
    web_container_name = f"va_web_{voter_id}"

    # Compose network
    network_name = "loki-implementation-thesis2025_default"

    # Images built by docker-compose
    api_image = "loki-implementation-thesis2025-va_api:latest"
    web_image = "loki-implementation-thesis2025-va_web:latest"

    # Per-voter volume for DUCKDB
    volume_name = f"va_duckdb_{voter_id}"

    # Ensure volume exists
    try:
        client.volumes.get(volume_name)
    except NotFound:
        client.volumes.create(name=volume_name)

    # Return if API container already exists (idempotency)
    existing_api = client.containers.list(filters={"name": api_container_name})
    existing_web = client.containers.list(filters={"name": web_container_name})
    if existing_api and existing_web:
        return api_container_name, web_container_name

    # ---- Start API container ----
    api_env = {
        "BB_API_URL": "http://bb_api:8000",
        "VOTER_SK_DECRYPTION_KEY": "Al43dQKlM/aAjb5zBNYXBQ==",
        "DUCKDB_PATH": "/duckdb/voter-keys.duckdb",
        "VOTER_ID": str(voter_id),
    }

    api_container = client.containers.run(
        image=api_image,
        name=api_container_name,
        detach=True,
        network=network_name,
        environment=api_env,
        volumes={volume_name: {"bind": "/duckdb", "mode": "rw"}},
        ports={"8000/tcp": None},  # Random host port; change if needed
    )

    # ---- Start Web container ----
    web_env = {
        "VITE_API_VOTINGAPP": f"http://{api_container_name}:8000"
    }

    web_container = client.containers.run(
        image=web_image,
        name=web_container_name,
        detach=True,
        network=network_name,
        environment=web_env,
        ports={"80/tcp": None},  # Random host port; change if needed
    )

    return api_container_name, web_container_name

if __name__ == "__main__":
    voter_id = input("Enter voter ID: ").strip()

    if not voter_id:
        print("Error: voter ID cannot be empty.")
        exit(1)

    create_va_instance(voter_id)