$ErrorActionPreference = "Stop"
Set-Location (Join-Path $PSScriptRoot "..")

if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    throw "Docker Desktop/Engine is required. Install Docker, then run this command again."
}

if (-not (Test-Path ".env")) {
    Copy-Item ".env.example" ".env"
    Write-Host "Created .env with safe localhost defaults. Add SARVAM_API_KEY or GEMINI_API_KEY for ingestion."
}

$composeArgs = @("-f", "docker-compose.yml")
if (Test-Path (Join-Path (Split-Path $PSScriptRoot -Parent) "..\backend\Dockerfile")) {
    $composeArgs += @("-f", "docker-compose.source.yml")
    Write-Host "Using the sibling MemoryOS backend source for this monorepo checkout."
}
try {
    docker compose @composeArgs --profile ui up -d --pull missing
} catch {
    Write-Host "The published backend/console image could not be pulled." -ForegroundColor Yellow
    Write-Host "If this is a public checkout, make the GHCR packages public or set SYNTARUS_*_IMAGE in .env."
    throw
}
& (Join-Path $PSScriptRoot "doctor.ps1")
$consolePort = if ($env:CONSOLE_PORT) { $env:CONSOLE_PORT } else { "5173" }
Write-Host "Continuum is ready: http://127.0.0.1:$consolePort"
