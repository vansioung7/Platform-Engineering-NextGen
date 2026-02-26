# 04 - API Contracts

## Endpoints

- `GET /health`
- `POST /generate/terraform/preview`
- `POST /generate/terraform/download`
- `POST /generate/helm/preview`
- `POST /generate/helm/download`
- `POST /generate/platform/preview`
- `POST /generate/platform/download`

## Platform Request Model

Required:
- `cloud`: `aws | azure | gcp`

Optional:
- `existing_cluster` (default `false`)
- `terraform_context`
- `helm_context`
- `terraform_template`
- `helm_template`

## Response Modes

- Preview: JSON with file paths and content.
- Download: ZIP stream of generated artifacts.

## Error Semantics

- `404`: template not found.
- `400`: rendering/generation failure.
