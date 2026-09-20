$ErrorActionPreference = "Stop"
Set-Location (Join-Path $PSScriptRoot "..")

if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    throw "Docker Desktop/Engine is required. Install Docker, then run this command again."
}

if (-not (Test-Path ".env")) {
    Copy-Item ".env.example" ".env"
    Write-Host "Created .env with safe localhost defaults. Add SARVAM_API_KEY or GEMINI_API_KEY for ingestion."
}

docker compose --profile ui up -d --pull missing
& (Join-Path $PSScriptRoot "doctor.ps1")
$consolePort = if ($env:CONSOLE_PORT) { $env:CONSOLE_PORT } else { "5173" }
Write-Host "Continuum is ready: http://127.0.0.1:$consolePort"
