# Closing and removing docker images
Write-Host "Closing and removing Docker images..." -ForegroundColor Green
docker compose down

# Removing data in docker volumes
Write-Host "Removing Docker data volumes..." -ForegroundColor Green
docker volume rm backendsystems_vs_data
docker volume rm backendsystems_db_data
docker volume rm backendsystems_ra_data

# Building Docker images
Write-Host "Building docker images..." -ForegroundColor Green
docker compose up --build -d

# Loops indefinitely until user chooses to exit
do {
    Write-Host " "  
    Write-Host "---------- Choose an option ----------"  -ForegroundColor Yellow
    Write-Host "1: Load election 1"
    Write-Host "2: Load election 2"
    Write-Host "3: Rerun application from scratch"
    Write-Host "4: Exit (closes and removes Docker images)"

    $choice = Read-Host "Enter your choice (1-4)"

    switch ($choice) {
        '1' {
            Write-Host "Loading election 1..." -ForegroundColor Green
            Invoke-RestMethod -Uri "http://localhost:8002/elections/load-file?name=election1.json" -Method Post
        }
        '2' {
            Write-Host "Loading election 2..." -ForegroundColor Green
            Invoke-RestMethod -Uri "http://localhost:8002/elections/load-file?name=election2.json" -Method Post  
        }
        '3' {
            Write-Host "Rerun docker"  -ForegroundColor Green
            docker compose down
            ./run_backendsystems.ps1
        }
        '4' {
            Write-Host "Exiting. Closing and removing Docker images..." -ForegroundColor Green
            docker compose down
            exit
        }

        default {
            Write-Host "Invalid selection. Choose a number from 1-4"  -ForegroundColor Red
        }
    }

} while ($choice -ne '4')