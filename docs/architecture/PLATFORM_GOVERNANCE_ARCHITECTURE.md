# Platform Governance Architecture (GHA + OPA + Argo CD + Drift)

This document shows how orchestration, policy enforcement, and drift remediation interact across infrastructure and workloads.

## 1) System Interaction Architecture

```mermaid
flowchart LR
    Dev[Engineer / PR Author] --> GH[GitHub Repository]
    GH --> P1[infra-plan workflow]
    GH --> P2[infra-apply workflow]
    GH --> D1[infra-drift-detection workflow]
    GH --> D2[workload-drift-detection workflow]
    GH --> G1[drift-remediation-governance workflow]

    P1 --> TFPlan[Terraform Plan JSON]
    P2 --> TFApply[Terraform Apply]
    TFPlan --> OPA[OPA/Conftest Policies]
    OPA --> Gate{Policy Pass?}
    Gate -->|Yes| TFApply
    Gate -->|No| Block[Fail Workflow]

    TFApply --> Cloud[(Cloud Infra: AWS/Azure/GCP)]
    D1 --> Cloud
    D1 --> Native[Optional Native Cloud Checks]
    D1 --> DriftIssue[GitHub Drift Issue]

    D2 --> Helm[Helm Render + Lint]
    Helm --> KubeOPA[OPA Policies for K8s Manifests]
    D2 --> Argo[Argo CD App Sync/Health]
    KubeOPA --> WorkloadIssue[Workload Drift Issue]
    Argo --> WorkloadIssue

    DriftIssue --> Ticketing[drift-ticketing-and-notification]
    WorkloadIssue --> Ticketing
    Ticketing --> Jira[Jira Ticket]
    Ticketing --> Notify[Webhook/Chat Notification]

    Dev --> RemPR[Remediation PR]
    RemPR --> G1
    G1 --> VerifyInfra[Terraform Drift Re-verify]
    G1 --> VerifyWorkload[Argo CD Sync Re-verify]
    G1 --> Audit[Audit Artifact]
    G1 --> Close[Close Drift Issue + Optional Jira Transition]
```

## 2) Infrastructure Drift Detection and Closure

```mermaid
sequenceDiagram
    participant S as Scheduler / Dispatch
    participant GHA as infra-drift-detection
    participant TF as Terraform
    participant OPA as OPA (Conftest)
    participant GH as GitHub Issues
    participant GOV as drift-remediation-governance
    participant Cloud as Cloud Provider

    S->>GHA: Trigger infra drift run
    GHA->>TF: terraform init + plan -detailed-exitcode
    TF->>Cloud: Read actual infra state
    TF-->>GHA: Exit code 0/2 + tfplan
    alt Drift detected (exit code 2)
        GHA->>TF: terraform show -json tfplan
        GHA->>OPA: Policy check on plan JSON
        GHA->>GH: Open drift issue (+ artifacts)
    else No drift (exit code 0)
        GHA-->>S: No issue created
    end

    note over GOV: PR with Drift Type: infra is merged
    GOV->>TF: terraform plan -detailed-exitcode
    alt Exit code 0
        GOV->>GH: Close drift issue, add audit record
    else Exit code 2
        GOV->>GH: Keep issue open, comment for follow-up
    end
```

## 3) Workload Drift Detection with Argo CD

```mermaid
sequenceDiagram
    participant S as Scheduler / Dispatch
    participant GHA as workload-drift-detection
    participant Helm as Helm
    participant OPA as OPA (K8s policies)
    participant Argo as Argo CD
    participant GH as GitHub Issues
    participant GOV as drift-remediation-governance

    S->>GHA: Trigger workload drift run
    GHA->>Helm: helm lint + helm template
    GHA->>OPA: Validate rendered manifests
    GHA->>Argo: Query app sync/health
    alt Policy fail or Argo not Synced
        GHA->>GH: Open workload-drift issue (+ artifacts)
    else Healthy + Synced
        GHA-->>S: No issue created
    end

    note over GOV: PR with Drift Type: workload is merged
    GOV->>Argo: Re-check app sync status
    alt Synced
        GOV->>GH: Close workload drift issue + audit
    else Not Synced
        GOV->>GH: Keep issue open for manual follow-up
    end
```

