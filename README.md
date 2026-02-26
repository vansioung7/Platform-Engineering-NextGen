# Terraform + Helm Generator Platform (MVP)

This service generates Terraform and Helm chart artifacts on demand from templates.

## What it does
- Generates Terraform module files from typed API payloads.
- Generates Helm chart files from typed API payloads.
- Returns generated files as JSON (`/preview`) or as ZIP downloads (`/download`).
- Supports AWS, Azure, and GCP with one unified platform endpoint.
- Supports existing clusters by generating namespace + workload artifacts without Terraform cluster creation.

## Cloud compatibility
Terraform templates included:
- AWS: `aws-eks`
- Azure: `azure-aks`
- GCP: `gcp-gke`

Helm templates included:
- Generic: `basic`
- Azure AKS-oriented: `aks-basic`
- GCP GKE-oriented: `gke-basic`

## Quick start
```bash
python -m venv .venv
. .venv/Scripts/Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Open docs: `http://127.0.0.1:8000/docs`

## API
- `POST /generate/terraform/preview`
- `POST /generate/terraform/download`
- `POST /generate/helm/preview`
- `POST /generate/helm/download`
- `POST /generate/platform/preview`
- `POST /generate/platform/download`

## GitHub Actions + OPA + Drift
Repository scaffolding is included for infrastructure orchestration:
- PR orchestration: `.github/workflows/infra-plan.yml`
- Apply orchestration: `.github/workflows/infra-apply.yml`
- Scheduled drift detection: `.github/workflows/infra-drift-detection.yml`
- OPA policy checks: `policies/terraform/deny.rego`
- Optional native cloud checks with toggle (`enable_native_checks`) for `aws` / `azure` / `gcp`
- OIDC auth steps are included for AWS/Azure/GCP workflows (configure cloud-specific repo/environment variables)

Implementation guide:
- `docs/INFRA_GOVERNANCE_AND_ORCHESTRATION.md`
- `docs/OIDC_SETUP.md`
- `docs/DRIFT_GOVERNANCE_WORKFLOW.md`

## Unified platform payload (new cluster)
```json
{
  "cloud": "aws",
  "existing_cluster": false,
  "terraform_context": {
    "project": "platform",
    "aws_region": "us-east-1",
    "cluster_name": "platform-eks"
  },
  "helm_context": {
    "chart_name": "payments",
    "chart_version": "0.1.0",
    "app_version": "1.0.0",
    "namespace": "payments",
    "create_namespace": true,
    "image_repository": "nginx",
    "image_tag": "1.27",
    "replica_count": 2,
    "service_port": 80,
    "container_port": 80
  }
}
```

## Unified platform payload (existing cluster)
```json
{
  "cloud": "gcp",
  "existing_cluster": true,
  "helm_context": {
    "chart_name": "orders",
    "chart_version": "0.1.0",
    "app_version": "1.0.0",
    "namespace": "orders",
    "create_namespace": true,
    "image_repository": "nginx",
    "image_tag": "1.27",
    "replica_count": 2,
    "service_port": 80,
    "container_port": 80,
    "load_balancer_type": "External"
  }
}
```

When `existing_cluster` is `true`, Terraform generation is skipped and only Helm artifacts are returned.

Use `cloud` values:
- `aws` (Terraform `aws-eks`, Helm `basic`)
- `azure` (Terraform `azure-aks`, Helm `aks-basic`)
- `gcp` (Terraform `gcp-gke`, Helm `gke-basic`)

Optional overrides are available:
- `terraform_template`
- `helm_template`

## Extending templates
Add a new folder under:
- `templates/terraform/<template-name>/...`
- `templates/helm/<template-name>/...`

Files ending in `.j2` are rendered via Jinja2 and emitted without `.j2`.
Non-`.j2` files are copied as-is.

## Pod scheduling controls
Helm context now supports pod affinity and anti-affinity keys:
- `affinity_enabled` (boolean)
- `affinity_type` (`podAffinity` or `podAntiAffinity`)
- `affinity_topology_key` (example: `kubernetes.io/hostname`)

Example (`helm_context`) for anti-affinity:
```json
{
  "chart_name": "orders",
  "chart_version": "0.1.0",
  "app_version": "1.0.0",
  "namespace": "orders",
  "create_namespace": true,
  "image_repository": "nginx",
  "image_tag": "1.27",
  "replica_count": 2,
  "service_port": 80,
  "container_port": 80,
  "cpu_request": "100m",
  "memory_request": "128Mi",
  "cpu_limit": "500m",
  "memory_limit": "512Mi",
  "affinity_enabled": true,
  "affinity_type": "podAntiAffinity",
  "affinity_topology_key": "kubernetes.io/hostname"
}
```

## HPA autoscaling controls
Helm context now supports HPA autoscaling and downscaling:
- `hpa_enabled` (boolean)
- `hpa_min_replicas` (number)
- `hpa_max_replicas` (number)
- `hpa_cpu_utilization_target` (percentage, set `0` to disable CPU metric)
- `hpa_memory_utilization_target` (percentage, set `0` to disable memory metric)

Example HPA settings (`helm_context`):
```json
{
  "hpa_enabled": true,
  "hpa_min_replicas": 2,
  "hpa_max_replicas": 10,
  "hpa_cpu_utilization_target": 70,
  "hpa_memory_utilization_target": 80
}
```

## Istio mesh controls (ingress/egress)
Helm context now supports Istio traffic management:
- `istio_enabled` (boolean)
- `istio_ingress_enabled` (boolean)
- `istio_egress_enabled` (boolean)
- `istio_gateway_create` (boolean)
- `istio_gateway_name`
- `istio_gateway_namespace`
- `istio_gateway_host`
- `istio_gateway_port`
- `istio_gateway_ref` (used when gateway is not created by this chart, example: `istio-system/public-gateway`)
- `istio_virtual_service_host`
- `istio_virtual_service_prefix`
- `istio_egress_host`
- `istio_egress_port`
- `istio_egress_protocol` (example: `HTTPS`)

Example (`helm_context`) enabling both ingress and egress:
```json
{
  "istio_enabled": true,
  "istio_ingress_enabled": true,
  "istio_egress_enabled": true,
  "istio_gateway_create": false,
  "istio_gateway_name": "public-gateway",
  "istio_gateway_namespace": "istio-system",
  "istio_gateway_host": "orders.example.com",
  "istio_gateway_port": 80,
  "istio_gateway_ref": "istio-system/public-gateway",
  "istio_virtual_service_host": "orders.example.com",
  "istio_virtual_service_prefix": "/",
  "istio_egress_host": "api.stripe.com",
  "istio_egress_port": 443,
  "istio_egress_protocol": "HTTPS"
}
```

## Pod request throttling controls
Helm context now supports request throttling to pods (Istio sidecar required):
- `throttle_enabled` (boolean)
- `throttle_max_tokens` (number)
- `throttle_tokens_per_fill` (number)
- `throttle_fill_interval` (duration string like `1s`, `500ms`, `1m`)

Example (`helm_context`) for throttling:
```json
{
  "istio_enabled": true,
  "throttle_enabled": true,
  "throttle_max_tokens": 100,
  "throttle_tokens_per_fill": 100,
  "throttle_fill_interval": "1s"
}
```

This creates an Istio `EnvoyFilter` applying local inbound rate limiting at the pod sidecar.

## KEDA throttling-aware autoscaling
Use KEDA with Prometheus when you want autoscaling based on sustained throttling/load pressure.

Recommended behavior:
- Set `keda_enabled: true`
- Set `hpa_enabled: false` (avoid two autoscalers controlling the same Deployment)
- Keep throttling enabled with Istio if using local rate limit

KEDA parameters (`helm_context`):
- `keda_enabled` (boolean)
- `keda_min_replicas` (number)
- `keda_max_replicas` (number)
- `keda_polling_interval` (seconds)
- `keda_cooldown_period` (seconds)
- `keda_threshold` (string/number)
- `keda_activation_threshold` (string/number)
- `keda_prometheus_server_address` (URL)
- `keda_metric_name` (string)
- `keda_query` (Prometheus query)
- `keda_scale_up_stabilization_window` (seconds)
- `keda_scale_down_stabilization_window` (seconds)

Example query based on sustained 429 ratio from throttling:
```text
sum(rate(istio_requests_total{destination_workload="orders",response_code="429"}[5m]))
/
clamp_min(sum(rate(istio_requests_total{destination_workload="orders"}[5m])), 1)
```

Example (`helm_context`) KEDA block:
```json
{
  "hpa_enabled": false,
  "keda_enabled": true,
  "keda_min_replicas": 2,
  "keda_max_replicas": 20,
  "keda_polling_interval": 30,
  "keda_cooldown_period": 600,
  "keda_threshold": "0.05",
  "keda_activation_threshold": "0.01",
  "keda_prometheus_server_address": "http://prometheus.monitoring.svc.cluster.local:9090",
  "keda_metric_name": "orders_throttle_ratio",
  "keda_query": "sum(rate(istio_requests_total{destination_workload=\"orders\",response_code=\"429\"}[5m])) / clamp_min(sum(rate(istio_requests_total{destination_workload=\"orders\"}[5m])), 1)",
  "keda_scale_up_stabilization_window": 60,
  "keda_scale_down_stabilization_window": 600
}
```

## Metrics emission controls
Helm context now supports explicit metric emission for autoscaling and observability.

Parameters (`helm_context`):
- `metrics_enabled` (boolean)
- `metrics_app_enabled` (boolean)
- `metrics_app_path` (example: `/metrics`)
- `metrics_app_port` (number)
- `metrics_pod_monitor_enabled` (boolean)
- `metrics_pod_monitor_interval` (example: `30s`)
- `metrics_pod_monitor_scrape_timeout` (example: `10s`)

What gets emitted:
- Istio/Envoy sidecar metrics from pod port `15090` at `/stats/prometheus` (when `istio_enabled=true`)
- Optional app metrics endpoint from your container (`metrics_app_port` + `metrics_app_path`)

Generated resource:
- `PodMonitor` (`monitoring.coreos.com/v1`) per workload when enabled.

Example (`helm_context`) metrics block:
```json
{
  "metrics_enabled": true,
  "metrics_app_enabled": true,
  "metrics_app_path": "/metrics",
  "metrics_app_port": 9090,
  "metrics_pod_monitor_enabled": true,
  "metrics_pod_monitor_interval": "30s",
  "metrics_pod_monitor_scrape_timeout": "10s"
}
```

Prerequisites:
- Prometheus Operator (for `PodMonitor` CRD)
- Istio telemetry enabled if you rely on Istio request/throttle signals

## Prometheus + Grafana + logs + audit
The generated charts now include configuration for:
- Prometheus metric scraping via `PodMonitor` and optional `ServiceMonitor`
- Grafana-friendly log scraping annotations
- Application audit policy ConfigMap mounted into pods

Additional `helm_context` parameters:
- `metrics_service_monitor_enabled` (boolean)
- `logs_enabled` (boolean)
- `logs_format` (example: `json`)
- `logs_level` (example: `info`)
- `logs_provider` (example: `grafana-cloud` or `splunk`)
- `audit_enabled` (boolean)
- `audit_mode` (example: `strict`)
- `audit_include_request_body` (boolean)
- `audit_policy_version` (example: `v1`)

What is generated:
- `PodMonitor` for pod-level metrics
- `ServiceMonitor` for service-level metrics
- deployment annotations for Prometheus and Promtail/Grafana log scraping
- `ConfigMap` named `<chart_name>-audit-policy` mounted at `/etc/platform/audit/policy.yaml`

Operational prerequisites:
- Prometheus Operator CRDs (`PodMonitor`, `ServiceMonitor`)
- Prometheus datasource configured in Grafana
- Log collector (for example Promtail/Loki or Fluent Bit) honoring pod annotations
- Application should emit structured logs/audit events (env vars are injected by this chart)

## Logging provider support (Grafana Cloud + Splunk)
Logging now supports both providers through `logs_provider`:
- `grafana-cloud`
- `splunk`

Additional `helm_context` parameters:
- `logs_provider` (`grafana-cloud` or `splunk`)
- `logs_grafana_cloud_logs_url`
- `logs_grafana_cloud_tenant_id`
- `logs_grafana_cloud_auth_secret_name`
- `logs_grafana_cloud_auth_secret_create` (boolean)
- `logs_grafana_cloud_auth_user`
- `logs_grafana_cloud_auth_token`
- `logs_splunk_hec_url`
- `logs_splunk_index`
- `logs_splunk_source`
- `logs_splunk_sourcetype`
- `logs_splunk_token_secret_name`
- `logs_splunk_token_secret_create` (boolean)
- `logs_splunk_token`

Generated resources:
- `logs-grafana-secret.yaml` (optional secret creation)
- `logs-splunk-secret.yaml` (optional secret creation)

Example (`grafana-cloud`):
```json
{
  "logs_enabled": true,
  "logs_provider": "grafana-cloud",
  "logs_grafana_cloud_logs_url": "https://logs-prod-us-central1.grafana.net/loki/api/v1/push",
  "logs_grafana_cloud_tenant_id": "123456",
  "logs_grafana_cloud_auth_secret_name": "grafana-cloud-logs-auth",
  "logs_grafana_cloud_auth_secret_create": true,
  "logs_grafana_cloud_auth_user": "123456",
  "logs_grafana_cloud_auth_token": "<token>"
}
```

Example (`splunk`):
```json
{
  "logs_enabled": true,
  "logs_provider": "splunk",
  "logs_splunk_hec_url": "https://splunk-hec.example.com:8088/services/collector",
  "logs_splunk_index": "platform",
  "logs_splunk_source": "k8s",
  "logs_splunk_sourcetype": "_json",
  "logs_splunk_token_secret_name": "splunk-hec-token",
  "logs_splunk_token_secret_create": true,
  "logs_splunk_token": "<hec-token>"
}
```


## Unified telemetry support (metrics, traces, logs)
The chart now supports provider-backed telemetry export for all three signals.

Supported providers:
- `grafana-cloud`
- `splunk`

Telemetry parameters (`helm_context`):
- `telemetry_enabled`
- `telemetry_provider` (`grafana-cloud` or `splunk`)
- `telemetry_metrics_enabled`
- `telemetry_traces_enabled`
- `telemetry_logs_enabled`
- `telemetry_otlp_endpoint`
- `telemetry_otlp_protocol` (example: `http/protobuf`)
- `telemetry_auth_header_name` (example: `Authorization`)
- `telemetry_auth_secret_name`
- `telemetry_auth_secret_create`
- `telemetry_auth_token`

Generated telemetry resources:
- `telemetry-otlp-secret.yaml` (optional)
- Deployment envs for OTEL exporters:
  - `OTEL_EXPORTER_OTLP_ENDPOINT`
  - `OTEL_EXPORTER_OTLP_PROTOCOL`
  - `OTEL_EXPORTER_OTLP_HEADERS`
  - `OTEL_METRICS_EXPORTER`, `OTEL_TRACES_EXPORTER`, `OTEL_LOGS_EXPORTER`

Example (`grafana-cloud`):
```json
{
  "telemetry_enabled": true,
  "telemetry_provider": "grafana-cloud",
  "telemetry_metrics_enabled": true,
  "telemetry_traces_enabled": true,
  "telemetry_logs_enabled": true,
  "telemetry_otlp_endpoint": "https://otlp-gateway-prod-us-central-0.grafana.net/otlp",
  "telemetry_otlp_protocol": "http/protobuf",
  "telemetry_auth_header_name": "Authorization",
  "telemetry_auth_secret_name": "otel-auth",
  "telemetry_auth_secret_create": true,
  "telemetry_auth_token": "Bearer <grafana-token>"
}
```

Example (`splunk`):
```json
{
  "telemetry_enabled": true,
  "telemetry_provider": "splunk",
  "telemetry_metrics_enabled": true,
  "telemetry_traces_enabled": true,
  "telemetry_logs_enabled": true,
  "telemetry_otlp_endpoint": "https://ingest.<realm>.signalfx.com/v2/otlp",
  "telemetry_otlp_protocol": "http/protobuf",
  "telemetry_auth_header_name": "X-SF-Token",
  "telemetry_auth_secret_name": "otel-auth",
  "telemetry_auth_secret_create": true,
  "telemetry_auth_token": "<splunk-token>"
}
```

## Cluster operations management
The platform now supports additional cluster/workload operations controls.

Terraform node pool sizing:
- AWS/EKS:
  - `node_pool_min_size`
  - `node_pool_max_size`
  - `node_pool_desired_size`
  - `node_pool_instance_type`
  - `node_pool_max_unavailable`
- Azure/AKS:
  - `node_pool_min_size`
  - `node_pool_max_size`
  - `node_pool_desired_size`
  - `vm_size`
- GCP/GKE:
  - `node_pool_min_size`
  - `node_pool_max_size`
  - `node_pool_desired_size`
  - `machine_type`

Terraform patch windows:
- AKS:
  - `patch_day_of_week`
  - `patch_start_hour_utc`
- GKE:
  - `patch_window_start`
  - `patch_window_end`
  - `patch_window_recurrence`

Workload disruption budget (`helm_context`):
- `pdb_enabled`
- `pdb_min_available`
- `pdb_max_unavailable`

Namespace quota (`helm_context`):
- `quota_enabled`
- `quota_requests_cpu`
- `quota_requests_memory`
- `quota_limits_cpu`
- `quota_limits_memory`
- `quota_pods`

Generated resources:
- `pdb.yaml`
- `resourcequota.yaml`

Example (`helm_context`) for PDB + quota:
```json
{
  "pdb_enabled": true,
  "pdb_min_available": "1",
  "pdb_max_unavailable": "",
  "quota_enabled": true,
  "quota_requests_cpu": "4",
  "quota_requests_memory": "8Gi",
  "quota_limits_cpu": "8",
  "quota_limits_memory": "16Gi",
  "quota_pods": "40"
}
```

## Configurable node autoscaling and downscaling
Additional Terraform autoscaler controls are now available.

AWS EKS:
- `cluster_autoscaling_enabled`
  - Enables cluster-autoscaler discovery tags on node groups.
- Node scaling bounds already supported:
  - `node_pool_min_size`, `node_pool_max_size`, `node_pool_desired_size`

Azure AKS:
- `cluster_autoscaling_enabled`
- `cluster_autoscaler_scan_interval`
- `cluster_autoscaler_scale_down_delay_after_add`
- `cluster_autoscaler_scale_down_unneeded`
- `cluster_autoscaler_scale_down_unready`
- `cluster_autoscaler_scale_down_utilization_threshold`
- `cluster_autoscaler_max_graceful_termination_sec`

GCP GKE:
- `cluster_autoscaling_enabled`
- `cluster_autoscaling_profile` (`BALANCED` or `OPTIMIZE_UTILIZATION`)
- Node scaling bounds already supported:
  - `node_pool_min_size`, `node_pool_max_size`, `node_pool_desired_size`

## Grafana alerts for node/pod scaling
Yes. The chart now generates `PrometheusRule` alerts for scaling events that Grafana can visualize and route.

New `helm_context` parameters:
- `scaling_alerts_enabled`
- `scaling_alerts_provider` (set to `grafana`)
- `scaling_alerts_severity` (kept for compatibility; generated scaling alerts are forced to `info` for informational use)
- `scaling_alerts_pod_window` (example: `10m`)
- `scaling_alerts_node_window` (example: `10m`)
- `scaling_alerts_pod_for` (example: `1m`)
- `scaling_alerts_node_for` (example: `1m`)

Generated resource:
- `alerts-scaling-prometheusrule.yaml`

Default alert logic:
- Pod scaling: replica changes in deployment over the configured pod window.
- Node scaling: change in total allocatable cluster CPU over the configured node window.

Example:
```json
{
  "scaling_alerts_enabled": true,
  "scaling_alerts_provider": "grafana",
  "scaling_alerts_severity": "warning",
  "scaling_alerts_pod_window": "10m",
  "scaling_alerts_node_window": "10m",
  "scaling_alerts_pod_for": "1m",
  "scaling_alerts_node_for": "1m"
}
```


## High-severity alert for node quota usage
You can now enable a high-severity alert when node quota usage crosses a threshold (for example 75%).

New `helm_context` parameters:
- `quota_alerts_enabled`
- `quota_alerts_provider` (set to `grafana`)
- `quota_alerts_node_usage_threshold_percent` (set to `75`)
- `quota_alerts_node_for` (example: `2m`)

Alert behavior:
- Emits `severity: critical` and `priority: high`
- Trigger expression compares requested CPU vs allocatable node CPU

Example:
```json
{
  "quota_alerts_enabled": true,
  "quota_alerts_provider": "grafana",
  "quota_alerts_node_usage_threshold_percent": 75,
  "quota_alerts_node_for": "2m"
}
```
