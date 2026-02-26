# Infra Governance and Orchestration

This repository now includes a baseline GitHub Actions + OPA + Terraform state/drift model.

## What was added
- `.github/workflows/infra-plan.yml`
- `.github/workflows/infra-apply.yml`
- `.github/workflows/infra-drift-detection.yml`
- `.github/workflows/drift-ticketing-and-notification.yml`
- `.github/workflows/drift-remediation-governance.yml`
- `policies/terraform/deny.rego`
- `scripts/native-drift-check.sh`

## Target repository layout
Create these folders in the repo where Terraform is executed:

```text
infra/
  terraform/                 # Terraform root module to run
  env/
    dev/
      backend.hcl
    prod/
      backend.hcl
```

`infra/terraform` is the directory used by workflows.

## State management
Use remote state with locking. Recommended per cloud:

- AWS: S3 backend + DynamoDB lock table.
- Azure: AzureRM backend (Blob container; lease-based lock).
- GCP: GCS backend (object generation locking).

Example `backend.hcl` for AWS:

```hcl
bucket         = "my-tf-state-bucket"
key            = "platform/dev/terraform.tfstate"
region         = "us-east-1"
dynamodb_table = "my-tf-state-locks"
encrypt        = true
```

Example `backend.hcl` for Azure:

```hcl
resource_group_name  = "rg-tf-state"
storage_account_name = "mytfstateacct"
container_name       = "tfstate"
key                  = "platform/dev/terraform.tfstate"
```

Example `backend.hcl` for GCP:

```hcl
bucket = "my-tf-state-bucket"
prefix = "platform/dev"
```

## Orchestration flow
1. Pull request runs `infra-plan`.
2. `terraform plan` is exported to JSON.
3. OPA policies run through `conftest`.
4. Merge to `main` (or manual dispatch) runs `infra-apply`.
5. Scheduled `infra-drift-detection` runs daily and opens an issue on drift.
6. Optional cloud-native checks run when enabled.

All workflows use provider-aware OIDC auth (`aws`/`azure`/`gcp`) using `cloud_provider` input for manual runs, or `CLOUD_PROVIDER` repo variable for non-dispatch runs.

## Multi-cloud native check toggle
`infra-drift-detection` supports:
- `cloud_provider`: `aws`, `azure`, `gcp`
- `enable_native_checks`: `true`/`false`

For scheduled runs (no dispatch inputs), configure repository variables:
- `CLOUD_PROVIDER` (default fallback: `aws`)
- `ENABLE_NATIVE_CHECKS` (`true` or `false`)

Native commands are provider-specific and configurable via repository variables:
- `NATIVE_CHECKS_AWS_COMMAND`
- `NATIVE_CHECKS_AZURE_COMMAND`
- `NATIVE_CHECKS_GCP_COMMAND`

Examples:
- AWS: `aws configservice get-compliance-summary-by-config-rule`
- Azure: `az policy state summarize --top 20`
- GCP: `gcloud asset search-all-resources --scope=projects/$GOOGLE_CLOUD_PROJECT --limit=50`

When enabled, workflow runs `scripts/native-drift-check.sh` and uploads `native-check-report.md`.
Default native commands are built in when per-provider command variables are not set.

## Policy model
Current OPA policy enforces:
- Required `owner` tag for tagged resources.
- No `aws_security_group` SSH ingress (`22`) from `0.0.0.0/0`.

Extend by adding additional rules under `policies/terraform`.

## Required GitHub configuration
- Protect `main` branch and require `infra-plan` status checks.
- Configure GitHub Environments (`dev`, `prod`) and approval rules.
- Configure cloud credentials using OIDC for Actions runners.
- Ensure labels `infra` and `drift` exist (or let workflow auto-create on first issue).
- Set native-check variables if you enable native checks.

## OIDC variables by cloud
Set repository or environment variables used by workflows.

AWS:
- `AWS_ROLE_TO_ASSUME`
- `AWS_REGION` (optional; default `us-east-1`)

Azure:
- `AZURE_CLIENT_ID`
- `AZURE_TENANT_ID`
- `AZURE_SUBSCRIPTION_ID`

GCP:
- `GCP_WORKLOAD_IDENTITY_PROVIDER`
- `GCP_SERVICE_ACCOUNT`
- `GCP_PROJECT_ID`

Detailed setup guide:
- `docs/OIDC_SETUP.md`
- `docs/DRIFT_GOVERNANCE_WORKFLOW.md`
