$Root = Split-Path $PSScriptRoot -Parent
$Backend = Join-Path $Root "backend"
$Frontend = Join-Path $Root "frontend"

Write-Host "Opening the CryptoGuard API and the Vite app in two windows."
Write-Host "API:  http://127.0.0.1:8000/api/health"
Write-Host "App:  http://127.0.0.1:3000/"

Start-Process powershell -WorkingDirectory $Backend -ArgumentList "-NoExit", "-Command", "npm run dev"
Start-Process powershell -WorkingDirectory $Frontend -ArgumentList "-NoExit", "-Command", "npm run dev"
