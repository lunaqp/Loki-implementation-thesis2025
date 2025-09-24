# Script for running all the apps

# Ensure script stops on first error
$ErrorActionPreference = "Stop"

# Always start from the script's directory
Set-Location $PSScriptRoot

Write-Host "Running VotingApp API on port 5000"
# "/k" keeps the cmd window open after executing the commands.
Start-Process cmd -ArgumentList "/k cd VotingApp && npm run api"

Write-Host "Running VotingApp frontend on port 5173"
Start-Process cmd -ArgumentList "/k cd VotingApp && npm run dev"
Start-Process "http://localhost:5173"

Write-Host "Running BulletinBoard API on port 5001"
Start-Process cmd -ArgumentList "/k cd BulletinBoard && venv\Scripts\activate.bat && python -m api.apiBB"

Write-Host "All apps running" -ForegroundColor Green