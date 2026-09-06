# Start the katalog site locally (Django dev server on http://127.0.0.1:8000).
# Usage:  powershell -ExecutionPolicy Bypass -File run-local.ps1
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot
if (-not (Test-Path ".\.venv\Scripts\python.exe")) {
    Write-Error "No .venv found. See LOCAL_SETUP.md to create it."
}
.\.venv\Scripts\python.exe manage.py runserver 127.0.0.1:8000
