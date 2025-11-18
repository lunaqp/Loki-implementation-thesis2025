# Closing and removing docker images
Write-Host "Closing and removing Docker images..." -ForegroundColor Green
docker compose down

# Removing data in docker volumes
Write-Host "Removing Docker data volumes..." -ForegroundColor Green
docker volume rm votingapp_va_data

# Building Docker images
Write-Host "Building docker images..." -ForegroundColor Green
docker compose up --build -d

# Loops indefinitely until user chooses to exit
do {
    Write-Host " "  
    Write-Host "---------- Choose an option ----------"  -ForegroundColor Yellow
    Write-Host "5: Rerun application from scratch"
    Write-Host "6: Exit (closes and removes Docker images)"

    $choice = Read-Host "Enter your choice (5-6)"

    switch ($choice) {
        '5' {
            Write-Host "Rerun docker"  -ForegroundColor Green
            docker compose down
            ./run_votingapp.ps1
        }
        '6' {
            Write-Host "Exiting. Closing and removing Docker images..." -ForegroundColor Green
            docker compose down
            exit
        }
        default {
            Write-Host "Invalid selection. Choose either 5 or 6"  -ForegroundColor Red
        }
    }

} while ($choice -ne '6')