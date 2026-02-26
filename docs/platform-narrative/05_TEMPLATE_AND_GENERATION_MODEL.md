# 05 - Template and Generation Model

## Template Layout

- `templates/terraform/<template-name>/...`
- `templates/helm/<template-name>/...`

## Rendering Rules

- `.j2` files are rendered with Jinja2.
- Output removes `.j2` suffix.
- Non-`.j2` files are copied as-is.
- Undefined variables fail by design (`StrictUndefined`).

## Cloud Defaults

Terraform defaults:
- AWS: `aws-eks`
- Azure: `azure-aks`
- GCP: `gcp-gke`

Helm defaults:
- AWS: `basic`
- Azure: `aks-basic`
- GCP: `gke-basic`

## Extensibility Pattern

1. Add new template directory.
2. Define required context keys.
3. Validate with preview endpoint.
4. Validate ZIP output before release.
