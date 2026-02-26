#!/usr/bin/env bash
set -euo pipefail

provider="${1:-}"
if [[ -z "${provider}" ]]; then
  echo "usage: $0 <aws|azure|gcp>" >&2
  exit 2
fi

report="native-check-report.md"
timestamp="$(date -u +"%Y-%m-%dT%H:%M:%SZ")"

{
  echo "# Native Cloud Check Report"
  echo
  echo "- Timestamp (UTC): ${timestamp}"
  echo "- Provider: ${provider}"
  echo
} > "${report}"

run_configured_command() {
  local command_value="$1"
  local provider_name="$2"
  if [[ -z "${command_value}" ]]; then
    {
      echo "## ${provider_name}"
      echo
      echo "No native command configured. Set repository variable for this provider."
      echo
    } >> "${report}"
    return 0
  fi

  {
    echo "## ${provider_name}"
    echo
    echo '```text'
  } >> "${report}"

  set +e
  bash -lc "${command_value}" >> "${report}" 2>&1
  local rc=$?
  set -e

  {
    echo '```'
    echo
  } >> "${report}"

  if [[ ${rc} -ne 0 ]]; then
    echo "Native check command failed for ${provider_name}" >&2
    return ${rc}
  fi
}

run_or_default() {
  local configured="$1"
  local default_cmd="$2"
  local provider_name="$3"
  if [[ -n "${configured}" ]]; then
    run_configured_command "${configured}" "${provider_name}"
  else
    run_configured_command "${default_cmd}" "${provider_name}"
  fi
}

case "${provider}" in
  aws)
    run_or_default \
      "${NATIVE_CHECKS_AWS_COMMAND:-}" \
      "aws configservice get-compliance-summary-by-config-rule --region \"${AWS_REGION:-us-east-1}\"" \
      "AWS"
    ;;
  azure)
    run_or_default \
      "${NATIVE_CHECKS_AZURE_COMMAND:-}" \
      "az policy state summarize --top 20" \
      "Azure"
    ;;
  gcp)
    if [[ -z "${NATIVE_CHECKS_GCP_COMMAND:-}" && -z "${GOOGLE_CLOUD_PROJECT:-}" ]]; then
      echo "GOOGLE_CLOUD_PROJECT is required for default GCP native check command" >&2
      exit 2
    fi
    run_or_default \
      "${NATIVE_CHECKS_GCP_COMMAND:-}" \
      "gcloud asset search-all-resources --scope=\"projects/${GOOGLE_CLOUD_PROJECT}\" --limit=50 --format='table(name,assetType,location)'" \
      "GCP"
    ;;
  *)
    echo "unsupported provider: ${provider}" >&2
    exit 2
    ;;
esac

echo "Native check report created at ${report}"
