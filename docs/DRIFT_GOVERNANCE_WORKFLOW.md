# Drift Governance Workflow (End-to-End)

This defines the controlled path from detection to audited closure.

## Flow
1. `infra-drift-detection` detects drift and opens a GitHub issue with label `drift`.
2. `workload-drift-detection` checks Helm render/policy and Argo CD sync drift and opens a GitHub issue with labels `drift` + `workload-drift`.
3. `drift-ticketing-and-notification` runs on drift issue events:
- Optional Jira ticket creation.
- Optional webhook notification.
4. Engineer opens remediation PR using PR template metadata:
- Drift Issue
- Drift Type (`infra` or `workload`)
- Change Request ID
- Environment
- Cloud Provider
- ArgoCD App (required for workload drift)
- Jira Key (required only when Jira integration is enabled)
5. `drift-remediation-governance` pre-merge checks:
- Validates required metadata in PR body.
- Enforces minimum approval count.
6. On merge to `main`, `drift-remediation-governance` post-merge:
- Runs Terraform drift verification for `Drift Type: infra`.
- Runs Argo CD sync verification for `Drift Type: workload`.
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
  - `workload-drift-detection` (if chart/workload changes are part of normal PR flow)

## Required Variables
General:
- `MIN_DRIFT_PR_APPROVALS` (default `1`)
- `ENABLE_JIRA_INTEGRATION` (`true`/`false`)
- `ENABLE_DRIFT_NOTIFICATIONS` (`true`/`false`)
- `ENABLE_ARGOCD_CHECK` (`true`/`false`)

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

Workload drift:
- `WORKLOAD_CHART_PATH` (default fallback `infra/workloads/chart`)
- `WORKLOAD_NAMESPACE` (default fallback `default`)
- Optional `WORKLOAD_VALUES_FILE`
- `ARGOCD_APP_NAME` (used when not passed in manual dispatch)

## Required Secrets
Notifications:
- `DRIFT_NOTIFICATION_WEBHOOK_URL`

Jira:
- `JIRA_BASE_URL`
- `JIRA_USER_EMAIL`
- `JIRA_API_TOKEN`

Argo CD:
- `ARGOCD_SERVER`
- `ARGOCD_AUTH_TOKEN`

## Audit Artifact
Post-merge creates:
- `.artifacts/drift-audit-pr-<PR_NUMBER>.json`

This includes drift issue id, change request id, Jira key, env/provider, actor, merge commit, and verification result.
