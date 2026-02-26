# Infra Execution Root

This folder is used by GitHub Actions workflows for Terraform orchestration.

- Put runnable Terraform code in `infra/terraform`.
- Put per-environment backend config in `infra/env/<env>/backend.hcl`.

The workflows use:
- `infra/terraform` as Terraform working directory.
- `infra/env/dev/backend.hcl` or `infra/env/prod/backend.hcl` when present.

