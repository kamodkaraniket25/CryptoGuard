$Backend = Join-Path $PSScriptRoot "..\backend"
Set-Location $Backend
if (Test-Path ".\.venv\Scripts\python.exe") {
  .\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
} else {
  python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
}
