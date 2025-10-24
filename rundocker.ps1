# Closing and removing docker images
# Write-Host "Closing and removing Docker images..." -ForegroundColor Green
# docker compose down

# Removing data in docker volumes
Write-Host "Removing Docker data volumes..." -ForegroundColor Green
docker volume rm loki-implementation-thesis2025_vs_data
docker volume rm loki-implementation-thesis2025_db_data
docker volume rm loki-implementation-thesis2025_va_data

# Building Docker images
Write-Host "Building docker images..." -ForegroundColor Green
docker compose up --build -d

# Loops indefinitely until user chooses to exit
do {
    Write-Host " "  
    Write-Host "---------- Choose an option ----------"  -ForegroundColor Yellow
    Write-Host "1: Load election 1"
    Write-Host "2: Load election 2"
    Write-Host "3: Extract DuckDB file for Voting Server (timestamp table)"
    Write-Host "4: Extract DuckDB file for Voting App (voter keys)"
    Write-Host "5: Rerun application from scratch"
    Write-Host "6: Exit (closes and removes Docker images)"

    $choice = Read-Host "Enter your choice (1-6)"

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
            Write-Host "Extracting DuckDB database file for Voting Server"  -ForegroundColor Green
            docker cp loki-implementation-thesis2025-vs_api-1:/duckdb/voter-timestamps.duckdb ./voter-timestamps.duckdb
        }
        '4' {
            Write-Host "Extracting DuckDB database file for Voting App"  -ForegroundColor Green
            docker cp loki-implementation-thesis2025-va_api-1:/duckdb/voter-keys.duckdb ./voter-keys.duckdb
        }
        '5' {
            Write-Host "Rerun docker"  -ForegroundColor Green
            docker compose down
            ./rundocker.ps1
        }
        '6' {
            Write-Host "Exiting. Closing and removing Docker images..." -ForegroundColor Green
            docker compose down
        }
        default {
            Write-Host "Invalid selection. Choose a number from 1-6"  -ForegroundColor Red
        }
    }

} while ($choice -ne '6')