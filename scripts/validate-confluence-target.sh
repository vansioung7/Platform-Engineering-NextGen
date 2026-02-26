#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 3 ]]; then
  echo "usage: $0 <tenant_name> <expected_space_key> <config_path> [page_title]" >&2
  exit 2
fi

tenant_name="$1"
expected_space_key="$2"
config_path="$3"
page_title="${4:-}"

if [[ ! -f "${config_path}" ]]; then
  echo "Config file not found: ${config_path}" >&2
  exit 1
fi

set -a
# shellcheck source=/dev/null
source "${config_path}"
set +a

required_vars=(
  CONFLUENCE_BASE_URL
  CONFLUENCE_USER_EMAIL
  CONFLUENCE_API_TOKEN
  CONFLUENCE_SPACE_KEY
)

for v in "${required_vars[@]}"; do
  if [[ -z "${!v:-}" ]]; then
    echo "Missing required var in config: ${v}" >&2
    exit 1
  fi
done

if [[ "${CONFLUENCE_SPACE_KEY}" != "${expected_space_key}" ]]; then
  echo "Space key mismatch for tenant ${tenant_name}: expected ${expected_space_key}, got ${CONFLUENCE_SPACE_KEY}" >&2
  exit 1
fi

if [[ "${CONFLUENCE_BASE_URL}" != https://*atlassian.net* ]]; then
  echo "Unexpected Confluence base URL: ${CONFLUENCE_BASE_URL}" >&2
  exit 1
fi

if [[ -n "${page_title}" ]]; then
  case "${tenant_name}" in
    PE)
      if [[ "${page_title}" =~ [Ss][Rr][Ee]-?[Aa]gentic ]]; then
        echo "Cross-tenant marker detected in PE publish title: ${page_title}" >&2
        exit 1
      fi
      ;;
    SRE-AGENTIC)
      if [[ "${page_title}" =~ [Pp]latform[[:space:]]+[Ee]ngineering ]]; then
        echo "Cross-tenant marker detected in SRE-Agentic publish title: ${page_title}" >&2
        exit 1
      fi
      ;;
  esac
fi

echo "Confluence tenant validation passed for ${tenant_name} (${CONFLUENCE_SPACE_KEY})"

