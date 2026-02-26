# 03 - Request Flow and Sequence

## Runtime Flow

1. Client submits request to preview or download endpoint.
2. API validates payload contract.
3. Platform resolves template names from cloud + overrides.
4. Generator renders Terraform and/or Helm templates.
5. API returns JSON preview or ZIP artifact.

## Sequence (Platform Endpoint)

```text
Client -> FastAPI: POST /generate/platform/*
FastAPI -> Models: Validate payload
FastAPI -> Resolver: Select templates by cloud/override
alt existing_cluster=false
  FastAPI -> Generator: Generate terraform files
end
FastAPI -> Generator: Generate helm files
alt /preview
  FastAPI -> Client: JSON files
else /download
  FastAPI -> Client: ZIP stream
end
```

## Branching Rule

- `existing_cluster=true` skips Terraform generation.
- `existing_cluster=false` generates both Terraform and Helm artifacts.
