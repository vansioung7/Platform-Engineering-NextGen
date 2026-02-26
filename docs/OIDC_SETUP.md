# OIDC Setup for GitHub Actions (AWS, Azure, GCP)

This repository uses GitHub Actions OIDC to avoid long-lived cloud secrets.

## GitHub prerequisites
- Workflows already request `id-token: write`.
- Use GitHub Environment protection for `dev` and `prod`.
- Restrict federation to expected repo/branch/environment conditions.

## AWS (IAM Role + GitHub OIDC Provider)
1. Create IAM OIDC provider:
- Provider URL: `https://token.actions.githubusercontent.com`
- Audience: `sts.amazonaws.com`

2. Create IAM role for GitHub Actions and attach required least-privilege policies.

3. Add trust policy (replace placeholders):

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Federated": "arn:aws:iam::<AWS_ACCOUNT_ID>:oidc-provider/token.actions.githubusercontent.com"
      },
      "Action": "sts:AssumeRoleWithWebIdentity",
      "Condition": {
        "StringEquals": {
          "token.actions.githubusercontent.com:aud": "sts.amazonaws.com"
        },
        "StringLike": {
          "token.actions.githubusercontent.com:sub": [
            "repo:<ORG>/<REPO>:ref:refs/heads/main",
            "repo:<ORG>/<REPO>:environment:prod",
            "repo:<ORG>/<REPO>:environment:dev"
          ]
        }
      }
    }
  ]
}
```

4. Set GitHub variable:
- `AWS_ROLE_TO_ASSUME=arn:aws:iam::<AWS_ACCOUNT_ID>:role/<ROLE_NAME>`
- Optional: `AWS_REGION`

## Azure (App Registration + Federated Credential)
1. Create Azure AD App Registration (service principal).
2. Create federated credentials on that app:
- Issuer: `https://token.actions.githubusercontent.com`
- Audience: `api://AzureADTokenExchange`
- Subject examples:
  - `repo:<ORG>/<REPO>:ref:refs/heads/main`
  - `repo:<ORG>/<REPO>:environment:prod`
  - `repo:<ORG>/<REPO>:environment:dev`

3. Assign least-privilege RBAC roles at subscription/resource-group scope.

4. Set GitHub variables:
- `AZURE_CLIENT_ID`
- `AZURE_TENANT_ID`
- `AZURE_SUBSCRIPTION_ID`

## GCP (Workload Identity Federation)
1. Create workload identity pool and provider.
2. Map token attributes (example):
- `google.subject=assertion.sub`
- `attribute.repository=assertion.repository`
- `attribute.ref=assertion.ref`

3. Restrict provider by attribute condition (example):

```text
assertion.repository == "<ORG>/<REPO>" &&
(
  assertion.ref == "refs/heads/main" ||
  assertion.sub.startsWith("repo:<ORG>/<REPO>:environment:")
)
```

4. Create a GCP service account with least-privilege roles.
5. Allow principal set from the workload identity pool to impersonate service account (`roles/iam.workloadIdentityUser`).

6. Set GitHub variables:
- `GCP_WORKLOAD_IDENTITY_PROVIDER=projects/<PROJECT_NUMBER>/locations/global/workloadIdentityPools/<POOL>/providers/<PROVIDER>`
- `GCP_SERVICE_ACCOUNT=<SERVICE_ACCOUNT_EMAIL>`
- `GCP_PROJECT_ID=<PROJECT_ID>`

## Security hardening recommendations
- Use separate identities per environment (`dev` vs `prod`).
- Scope cloud roles to minimum permissions required by Terraform and native checks.
- Require manual approvals on `prod` GitHub Environment.
- Keep branch protection on `main` and require `infra-plan`.

