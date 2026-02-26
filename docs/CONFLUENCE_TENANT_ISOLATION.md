# Confluence Tenant Isolation (PE vs SRE-Agentic)

This repository enforces separation between:
- `PE` (Platform Engineering)
- `SRE-Agentic`

## Isolation Controls
1. Separate config templates:
- `config/confluence/confluence.pe.env.example`
- `config/confluence/confluence.sre-agentic.env.example`

2. Validation script (hard-fail on mismatch):
- `scripts/validate-confluence-target.sh`

3. Dedicated preflight workflows (no shared tenant selector):
- `.github/workflows/confluence-preflight-pe.yml`
- `.github/workflows/confluence-preflight-sre-agentic.yml`

## Required GitHub Secrets / Variables
PE workflow secrets:
- `PE_CONFLUENCE_BASE_URL`
- `PE_CONFLUENCE_USER_EMAIL`
- `PE_CONFLUENCE_API_TOKEN`

SRE-Agentic workflow secrets:
- `SRE_AGENTIC_CONFLUENCE_BASE_URL`
- `SRE_AGENTIC_CONFLUENCE_USER_EMAIL`
- `SRE_AGENTIC_CONFLUENCE_API_TOKEN`

SRE-Agentic workflow variable:
- `SRE_AGENTIC_SPACE_KEY` (example: `SREAGENTIC`)

## Guardrail Behavior
Validation fails if:
- Runtime config is missing required Confluence variables.
- `CONFLUENCE_SPACE_KEY` does not match expected tenant space key.
- Base URL is not an Atlassian Cloud URL.
- Page title appears to contain cross-tenant markers.

## Local Usage
Keep real env files local only:
- `confluence.pe.env`
- `confluence.sre-agentic.env`

These are ignored by git via `.gitignore`.

