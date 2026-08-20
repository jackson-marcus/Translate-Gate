# PowerShell task runner mirroring the Makefile.
# Usage: .\tasks.ps1 <task>   e.g. .\tasks.ps1 test
param([Parameter(Mandatory = $true)][string]$Task)

switch ($Task) {
    "install"    { uv sync --group dev }
    "lint"       { uv run ruff check .; uv run ruff format --check . }
    "format"     { uv run ruff check --fix .; uv run ruff format . }
    "test"       { uv run pytest --cov }
    "api"        { uv run uvicorn translategate.api.main:app --reload --port 8370 }
    "ui"         { $env:TRANSLATEGATE_API_URL = "http://localhost:8370"; uv run streamlit run src/translategate/ui/app.py --server.port 8871 }
    "mlflow"     { uv run mlflow ui --backend-store-uri sqlite:///mlflow.db --port 5038 }
    "docker-up"  { docker compose up --build -d }
    "docker-down"{ docker compose down }
    default      { Write-Host "Unknown task: $Task" }
}
