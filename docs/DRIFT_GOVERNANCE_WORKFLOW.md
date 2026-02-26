# Drift Governance Workflow (End-to-End)

This defines the controlled path from detection to audited closure.

## Flow
1. `infra-drift-detection` detects drift and opens a GitHub issue with label `drift`.
2. `drift-ticketing-and-notification` runs on drift issue events:
- Optional Jira ticket creation.
- Optional webhook notification.
3. Engineer opens remediation PR using PR template metadata:
- Drift Issue
- Change Request ID
- Environment
- Cloud Provider
- Jira Key (required only when Jira integration is enabled)
4. `drift-remediation-governance` pre-merge checks:
- Validates required metadata in PR body.
- Enforces minimum approval count.
5. On merge to `main`, `drift-remediation-governance` post-merge:
- Runs Terraform drift verification (`plan -detailed-exitcode`).
- Produces immutable audit JSON artifact.
- Closes drift issue if verification is clean.
- Optionally transitions Jira issue to done/closed.
- Optionally sends closure notification.

## Approval Mechanism
- Workflow enforces reviewer approvals (`MIN_DRIFT_PR_APPROVALS`).
- For production safety, also configure GitHub Environment approvals on `prod`.
- Branch protection should require:
  - `drift-remediation-governance / premerge-guard`
  - `infra-plan`

## Required Variables
General:
- `MIN_DRIFT_PR_APPROVALS` (default `1`)
- `ENABLE_JIRA_INTEGRATION` (`true`/`false`)
- `ENABLE_DRIFT_NOTIFICATIONS` (`true`/`false`)

Cloud and OIDC:
- `CLOUD_PROVIDER` (`aws|azure|gcp`, for scheduled flows)
- AWS: `AWS_ROLE_TO_ASSUME`, optional `AWS_REGION`
- Azure: `AZURE_CLIENT_ID`, `AZURE_TENANT_ID`, `AZURE_SUBSCRIPTION_ID`
- GCP: `GCP_WORKLOAD_IDENTITY_PROVIDER`, `GCP_SERVICE_ACCOUNT`, `GCP_PROJECT_ID`

Native checks (optional):
- `ENABLE_NATIVE_CHECKS` (`true`/`false`)
- Optional overrides:
  - `NATIVE_CHECKS_AWS_COMMAND`
  - `NATIVE_CHECKS_AZURE_COMMAND`
  - `NATIVE_CHECKS_GCP_COMMAND`

Jira integration:
- `JIRA_PROJECT_KEY`
- Optional: `JIRA_ISSUE_TYPE` (default `Task`)

## Required Secrets
Notifications:
- `DRIFT_NOTIFICATION_WEBHOOK_URL`

Jira:
- `JIRA_BASE_URL`
- `JIRA_USER_EMAIL`
- `JIRA_API_TOKEN`

## Audit Artifact
Post-merge creates:
- `.artifacts/drift-audit-pr-<PR_NUMBER>.json`

This includes drift issue id, change request id, Jira key, env/provider, actor, merge commit, and verification result.

