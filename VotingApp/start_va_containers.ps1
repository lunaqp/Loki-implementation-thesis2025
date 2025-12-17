# To create voter containers run in PowerShell:
# .\start_voter_va.ps1 101

# Exit immediately if a command fails
$ErrorActionPreference = "Stop"

# If no argument / voter ID is given, stop the script
if ($args.Count -lt 1) {
    Write-Host "Usage: $($MyInvocation.MyCommand.Name) <voter-id>"
    exit 1
}

# Voter ID is the first command-line argument
$VOTER_ID = $args[0]

$PROJECT_NAME = "voter_$VOTER_ID"

Write-Host "Starting VA for voter $VOTER_ID"
Write-Host "  compose project: $PROJECT_NAME"

# Set environment variable for this session
$env:VOTER_ID = $VOTER_ID

# Run Docker Compose
docker compose `
    -p $PROJECT_NAME `
    up -d --build va_api va_web
