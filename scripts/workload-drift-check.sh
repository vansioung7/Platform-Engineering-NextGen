#!/usr/bin/env bash
set -euo pipefail

mkdir -p .artifacts
report=".artifacts/workload-drift-report.md"
rendered=".artifacts/rendered-manifests.yaml"
drift_file=".artifacts/drift-status.env"

chart_path="${CHART_PATH:-infra/workloads/chart}"
namespace="${NAMESPACE:-default}"
values_file="${VALUES_FILE:-}"
enable_argocd="${ENABLE_ARGOCD_CHECK:-true}"
argocd_app="${ARGOCD_APP_NAME:-}"

{
  echo "# Workload Drift Report"
  echo
  echo "- Timestamp (UTC): $(date -u +"%Y-%m-%dT%H:%M:%SZ")"
  echo "- Chart Path: ${chart_path}"
  echo "- Namespace: ${namespace}"
  echo "- Argo CD Check Enabled: ${enable_argocd}"
  echo "- Argo CD App: ${argocd_app:-not-set}"
  echo
} > "${report}"

if [[ ! -d "${chart_path}" ]]; then
  {
    echo "Chart path does not exist: ${chart_path}"
  } >> "${report}"
  echo "WORKLOAD_DRIFT_DETECTED=false" > "${drift_file}"
  echo "drift_detected=false" >> "${GITHUB_OUTPUT}"
  exit 0
fi

helm lint "${chart_path}" >> "${report}" 2>&1

helm_args=(template drift-check "${chart_path}" --namespace "${namespace}")
if [[ -n "${values_file}" && -f "${values_file}" ]]; then
  helm_args+=(-f "${values_file}")
fi

helm "${helm_args[@]}" > "${rendered}"

if command -v conftest >/dev/null 2>&1 && [[ -d "policies/kubernetes" ]]; then
  {
    echo
    echo "## Policy Check (Conftest)"
    echo
    echo '```text'
  } >> "${report}"
  set +e
  conftest test "${rendered}" -p policies/kubernetes >> "${report}" 2>&1
  policy_rc=$?
  set -e
  echo '```' >> "${report}"
  if [[ ${policy_rc} -ne 0 ]]; then
    {
      echo
      echo "Policy check failed. Treating as actionable workload drift."
    } >> "${report}"
    echo "WORKLOAD_DRIFT_DETECTED=true" > "${drift_file}"
    echo "drift_detected=true" >> "${GITHUB_OUTPUT}"
    exit 0
  fi
fi

drift_detected="false"

if [[ "${enable_argocd}" == "true" ]]; then
  if [[ -z "${argocd_app}" ]]; then
    echo "ARGOCD_APP_NAME is required when Argo CD check is enabled" >> "${report}"
    echo "WORKLOAD_DRIFT_DETECTED=true" > "${drift_file}"
    echo "drift_detected=true" >> "${GITHUB_OUTPUT}"
    exit 0
  fi
  if [[ -z "${ARGOCD_SERVER:-}" || -z "${ARGOCD_AUTH_TOKEN:-}" ]]; then
    echo "ARGOCD_SERVER and ARGOCD_AUTH_TOKEN are required when Argo CD check is enabled" >> "${report}"
    echo "WORKLOAD_DRIFT_DETECTED=true" > "${drift_file}"
    echo "drift_detected=true" >> "${GITHUB_OUTPUT}"
    exit 0
  fi

  set +e
  argocd app get "${argocd_app}" \
    --server "${ARGOCD_SERVER}" \
    --auth-token "${ARGOCD_AUTH_TOKEN}" \
    --grpc-web \
    --refresh \
    -o json > .artifacts/argocd-app.json 2>> "${report}"
  argo_rc=$?
  set -e
  if [[ ${argo_rc} -ne 0 ]]; then
    echo "Argo CD query failed. Treating as drift for operator review." >> "${report}"
    drift_detected="true"
  else
    sync_status="$(jq -r '.status.sync.status // "Unknown"' .artifacts/argocd-app.json)"
    health_status="$(jq -r '.status.health.status // "Unknown"' .artifacts/argocd-app.json)"
    {
      echo
      echo "## Argo CD Status"
      echo
      echo "- Sync: ${sync_status}"
      echo "- Health: ${health_status}"
    } >> "${report}"
    if [[ "${sync_status}" != "Synced" ]]; then
      drift_detected="true"
    fi
  fi
fi

echo "WORKLOAD_DRIFT_DETECTED=${drift_detected}" > "${drift_file}"
echo "drift_detected=${drift_detected}" >> "${GITHUB_OUTPUT}"

