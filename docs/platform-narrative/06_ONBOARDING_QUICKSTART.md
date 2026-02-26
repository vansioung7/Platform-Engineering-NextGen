# 06 - Onboarding Quickstart

## Local Setup

```powershell
cd "C:\workspace\Platform Engineering"
python -m venv .venv
. .venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload
```

## Validate Service

- Health: `GET http://127.0.0.1:8000/health`
- API docs: `http://127.0.0.1:8000/docs`

## First Useful Calls

- Preview: `POST /generate/platform/preview`
- Artifact bundle: `POST /generate/platform/download`

## Where to Start in Code

- API orchestration: `app/main.py`
- Contracts: `app/models.py`
- Rendering engine: `app/generators.py`
