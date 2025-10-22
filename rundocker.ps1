# Closing and removing docker images
Write-Host "Closing and removing Docker images..." -ForegroundColor Green
docker compose down

# Removing data in docker volumes
Write-Host "Removing Docker data volumes..." -ForegroundColor Green
docker volume rm loki-implementation-thesis2025_vs_data
docker volume rm loki-implementation-thesis2025_db_data

# Building Docker images
Write-Host "Building docker images..." -ForegroundColor Green
docker compose up --build -d

Write-Host "Ready for elections" -ForegroundColor Green

# Decide which election to load
$choice = Read-Host "Enter '1' to to load election 1 or '2' to load election 2"

if ($choice -eq '1') {
    Write-Host "Loading election 1..." -ForegroundColor Green
    Invoke-RestMethod -Uri "http://localhost:8002/elections/load-file?name=election1.json" -Method Post
}
elseif ($choice -eq '2') {
    Write-Host "Loading election 2..." -ForegroundColor Green
    Invoke-RestMethod -Uri "http://localhost:8002/elections/load-file?name=election2.json" -Method Post
}
else {
    Write-Host "Invalid choice." -ForegroundColor Red
}