#### functions ####

# Setup virtual python environment
function Setup-Venv {
    param (
        [string[]]$Dependencies   # List of pip packages to install
    )

	Write-Host "Creating virtual environment in $($pwd.Path)"
	python -m venv venv

	Write-Host "Activating virtual environment..."
	& .\venv\Scripts\Activate.ps1

	Write-Host "Installing Python dependencies..."
	pip install @Dependencies
}

# Create .env file if it doesn’t exist
function Create-Dotenv {
	param (
	[string[]]$Lines
	)

	try {
		if (-Not (Test-Path ".env")) {
			New-Item -Path ".env" -ItemType File -Force | Out-Null
			foreach ($line in $Lines) {
				Add-Content -Path ".env" -Value $line
			}
			Write-Host ".env file created."
		} else {
			Write-Host ".env file already exists."
		}
	} catch {
		Write-Host "Error setting up .env file in $($pwd.Path). Check manually." -ForegroundColor Red
	}
}

# Setting up virtual environments and .env files
# Ensure script stops on first error
$ErrorActionPreference = "Stop"

# Always start from the script's directory
Set-Location $PSScriptRoot

#---------------------------------------------------------------- Voting App ----------------------------------------------------------------#

Write-Host "Setting up VotingApp Python and Node environments..." -ForegroundColor Yellow

# Navigate to VotingApp api-folder
Set-Location .\VotingApp\api

# Create Python venv
Write-Host "Creating virtual environment..."
Setup-Venv -Dependencies @("flask", "python-dotenv", "requests")

# Create .env file if it doesn’t exist
Write-Host "Creating .env file..."
Create-Dotenv -Lines @("FLASK_APP=apiVA.py", "FLASK_ENV=development")

# Go back to VotingApp root
Set-Location ..

# Install Node dependencies
if (Test-Path "package.json") {
    Write-Host "Installing Node dependencies..."
    npm install
} else {
    Write-Host "No package.json found, skipping npm install."
}

Write-Host "VotingApp Setup completed!" -ForegroundColor Green

#-------------------------------------------------------------- BulletinBoard --------------------------------------------------------------#

Write-Host "Setting up BulletinBoard Python environment..." -ForegroundColor Yellow

# Go to BulletinBoard directory
Set-Location ..\BulletinBoard

# Create Python venv
Write-Host "Creating virtual environment..."
Setup-Venv -Dependencies @("flask", "python-dotenv", "requests", "psycopg[binary]")

# Create .env file if it doesn’t exist
Write-Host "Creating .env file..."
Create-Dotenv -Lines @("FLASK_APP=apiBB.py", "FLASK_ENV=development")

Write-Host "BulletinBoard Setup completed!" -ForegroundColor Green

#----------------------------------------------------------- RegistrationAuthority -----------------------------------------------------------#

Write-Host "Setting up RegistrationAuthority Python environment..." -ForegroundColor Yellow

# Go to RegistrationAuthority directory
Set-Location ..\RegistrationAuthority

# Create Python venv
Write-Host "Creating virtual environment..."
Setup-Venv -Dependencies @("flask", "python-dotenv", "requests", "psycopg[binary]")

# Create .env file if it doesn’t exist
Write-Host "Creating .env file..."
Create-Dotenv -Lines @("FLASK_APP=apiRA.py", "FLASK_ENV=development")


Write-Host "RegistrationAuthority Setup completed!" -ForegroundColor Green