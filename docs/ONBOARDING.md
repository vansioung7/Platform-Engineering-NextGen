# Platform Onboarding Guide

## Purpose

This guide gets a new engineer productive on the Terraform + Helm Generator Platform.

## What You Are Working On

The platform is a FastAPI service that:
- Generates Terraform artifacts from templates.
- Generates Helm chart artifacts from templates.
- Supports a unified `/generate/platform/*` flow for AWS, Azure, and GCP.
- Returns either JSON previews or ZIP bundles.

Core code:
- `app/main.py` (API and flow orchestration)
- `app/models.py` (request contracts)
- `app/generators.py` (template rendering and ZIP packaging)

Templates:
- `templates/terraform/<template-name>/...`
- `templates/helm/<template-name>/...`

## Prerequisites

- Python 3.11+ recommended.
- PowerShell terminal on Windows.
- `pip` available in your Python installation.

## Day-1 Setup

```powershell
cd "C:\workspace\Platform Engineering"
python -m venv .venv
. .venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Service URLs:
- Swagger UI: `http://127.0.0.1:8000/docs`
- Health: `http://127.0.0.1:8000/health`

## Quick Smoke Test

### Health
```powershell
curl http://127.0.0.1:8000/health
```

Expected response:
```json
{"status":"ok"}
```

### Platform Preview (Existing Cluster)
```powershell
curl -X POST "http://127.0.0.1:8000/generate/platform/preview" ^
  -H "Content-Type: application/json" ^
  -d "{\"cloud\":\"gcp\",\"existing_cluster\":true,\"helm_context\":{\"chart_name\":\"orders\",\"chart_version\":\"0.1.0\",\"app_version\":\"1.0.0\",\"namespace\":\"orders\",\"create_namespace\":true,\"image_repository\":\"nginx\",\"image_tag\":\"1.27\",\"replica_count\":2,\"service_port\":80,\"container_port\":80}}"
```

Expected behavior:
- `terraform.template` is `null`.
- `helm.files` contains rendered chart files.

### Platform Download
```powershell
curl -X POST "http://127.0.0.1:8000/generate/platform/download" ^
  -H "Content-Type: application/json" ^
  -d "{\"cloud\":\"aws\",\"existing_cluster\":false,\"terraform_context\":{\"project\":\"platform\",\"aws_region\":\"us-east-1\",\"cluster_name\":\"platform-eks\"},\"helm_context\":{\"chart_name\":\"payments\",\"chart_version\":\"0.1.0\",\"app_version\":\"1.0.0\",\"namespace\":\"payments\",\"create_namespace\":true,\"image_repository\":\"nginx\",\"image_tag\":\"1.27\",\"replica_count\":2,\"service_port\":80,\"container_port\":80}}" ^
  -o platform-aws.zip
```

## How the Platform Chooses Templates

Defaults in `app/main.py`:
- Terraform: `aws-eks`, `azure-aks`, `gcp-gke`
- Helm: `basic`, `aks-basic`, `gke-basic`

Rules:
- `existing_cluster = true` => skip Terraform generation.
- You can override defaults with:
  - `terraform_template`
  - `helm_template`

## Adding or Updating Templates

1. Create a template folder:
   - `templates/terraform/<new-name>/...`
   - `templates/helm/<new-name>/...`
2. Put Jinja templates in `.j2` files.
3. Keep static files without `.j2`.
4. Validate via `/preview` endpoint before using `/download`.

Rendering behavior (`app/generators.py`):
- `.j2` files are rendered and emitted without `.j2` suffix.
- Undefined variables fail fast (`StrictUndefined`).

## Common Development Tasks

- Add a new endpoint: update `app/main.py`.
- Add request fields: update `app/models.py` and relevant templates.
- Change rendering behavior: update `TemplateGenerator` in `app/generators.py`.
- Update architecture docs: `docs/PLATFORM_DESIGN_DOC.md` and `docs/architecture/`.

## Troubleshooting

- `404 Template not found`:
  - Verify template path and name under `templates/<type>/<name>`.
- `400 Generation failed`:
  - Missing required Jinja variable in context.
  - Check payload keys and template references.
- Empty/missing output files:
  - Confirm files exist in template folder and extension rules are correct.

## Engineering Expectations

- Keep templates cloud-appropriate and explicit.
- Prefer additive changes to preserve backward compatibility.
- Validate with both preview and download paths.
- Document any new template contexts in `README.md`.

## Related Docs

- `README.md`
- `docs/PLATFORM_DESIGN_DOC.md`
- `docs/architecture/platform-architecture.png`
