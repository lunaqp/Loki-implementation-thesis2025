# Prompt for voter ID
$voterId = Read-Host "Enter voter ID"

if ([string]::IsNullOrWhiteSpace($voterId)) {
    Write-Host "Error: voter ID cannot be empty." -ForegroundColor Red
    exit
}

$apiContainer = "va_api_$voterId"
$webContainer = "va_web_$voterId"
$volumeName   = "va_duckdb_$voterId"

$apiImage = "loki-implementation-thesis2025-va_api:latest"
$webImage = "loki-implementation-thesis2025-va_web:latest"

$network = "loki-implementation-thesis2025_default"

# Check if containers already exist
$existingApi = docker ps -a --format "{{.Names}}" | Select-String "^$apiContainer$"
$existingWeb = docker ps -a --format "{{.Names}}" | Select-String "^$webContainer$"

if ($existingApi -and $existingWeb) {
    Write-Host "Instance for voter $voterId already exists." -ForegroundColor Yellow
    exit
}

# Create volume if it does not exist
$volumeExists = docker volume inspect $volumeName 2>$null
if (!$volumeExists) {
    docker volume create $volumeName | Out-Null
}

Write-Host "Starting API container $apiContainer ..."

docker run -d `
    --name $apiContainer `
    --network $network `
    -e "BB_API_URL=http://bb_api:8000" `
    -e "VOTER_SK_DECRYPTION_KEY=Al43dQKlM/aAjb5zBNYXBQ==" `
    -e "DUCKDB_PATH=/duckdb/voter-keys.duckdb" `
    -e "VOTER_ID=$voterId" `
    -v "$volumeName:/duckdb" `
    $apiImage | Out-Null

Write-Host "Starting WEB container $webContainer ..."

docker run -d `
    --name $webContainer `
    --network $network `
    -e "VITE_API_VOTINGAPP=http://$apiContainer:8000" `
    $webImage | Out-Null

Write-Host "Instance created successfully:" -ForegroundColor Green
Write-Host "  API: $apiContainer"
Write-Host "  WEB: $webContainer"
