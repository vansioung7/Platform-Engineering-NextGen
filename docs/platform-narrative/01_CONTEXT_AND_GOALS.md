# 01 - Context and Goals

## Platform Purpose

The platform generates infrastructure and workload artifacts from templates:
- Terraform artifacts for cluster/infrastructure setup.
- Helm artifacts for workload deployment.

## Problems It Solves

- Standardizes environment bootstrapping across clouds.
- Reduces copy/paste drift in IaC and chart scaffolding.
- Speeds delivery through preview and ZIP packaging APIs.

## Scope

In scope:
- Deterministic template rendering.
- Cloud-aware defaults (AWS, Azure, GCP).
- Existing-cluster mode (Helm-only output).

Out of scope:
- Executing `terraform apply` or `helm install`.
- Long-running orchestration/state management.
