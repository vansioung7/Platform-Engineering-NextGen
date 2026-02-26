from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse, StreamingResponse

from app.generators import GeneratedFile, TemplateGenerator, to_zip
from app.models import GenerationRequest, PlatformGenerateRequest


app = FastAPI(title="Terraform + Helm Generator", version="0.1.0")

templates_dir = Path(__file__).resolve().parent.parent / "templates"
generator = TemplateGenerator(templates_dir)

TERRAFORM_TEMPLATE_BY_CLOUD = {
    "aws": "aws-eks",
    "azure": "azure-aks",
    "gcp": "gcp-gke",
}

HELM_TEMPLATE_BY_CLOUD = {
    "aws": "basic",
    "azure": "aks-basic",
    "gcp": "gke-basic",
}


def _generate_or_404(template_type: str, req: GenerationRequest):
    try:
        return generator.generate(template_type=template_type, template_name=req.template, context=req.context)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Generation failed: {exc}") from exc


def _resolve_platform_templates(req: PlatformGenerateRequest) -> tuple[str | None, str]:
    terraform_template = None if req.existing_cluster else (req.terraform_template or TERRAFORM_TEMPLATE_BY_CLOUD[req.cloud])
    helm_template = req.helm_template or HELM_TEMPLATE_BY_CLOUD[req.cloud]
    return terraform_template, helm_template


def _prefix_files(files: list[GeneratedFile], prefix: str) -> list[GeneratedFile]:
    return [GeneratedFile(path=f"{prefix}/{item.path}", content=item.content) for item in files]


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/generate/terraform/preview")
def terraform_preview(req: GenerationRequest):
    files = _generate_or_404("terraform", req)
    return JSONResponse({"files": [{"path": f.path, "content": f.content} for f in files]})


@app.post("/generate/terraform/download")
def terraform_download(req: GenerationRequest):
    files = _generate_or_404("terraform", req)
    blob = to_zip(files)
    return StreamingResponse(
        iter([blob]),
        media_type="application/zip",
        headers={"Content-Disposition": f"attachment; filename=terraform-{req.template}.zip"},
    )


@app.post("/generate/helm/preview")
def helm_preview(req: GenerationRequest):
    files = _generate_or_404("helm", req)
    return JSONResponse({"files": [{"path": f.path, "content": f.content} for f in files]})


@app.post("/generate/helm/download")
def helm_download(req: GenerationRequest):
    files = _generate_or_404("helm", req)
    blob = to_zip(files)
    return StreamingResponse(
        iter([blob]),
        media_type="application/zip",
        headers={"Content-Disposition": f"attachment; filename=helm-{req.template}.zip"},
    )


@app.post("/generate/platform/preview")
def platform_preview(req: PlatformGenerateRequest):
    terraform_template, helm_template = _resolve_platform_templates(req)

    terraform_files: list[GeneratedFile] = []
    if terraform_template:
        terraform_files = _generate_or_404(
            "terraform", GenerationRequest(template=terraform_template, context=req.terraform_context)
        )

    helm_files = _generate_or_404("helm", GenerationRequest(template=helm_template, context=req.helm_context))

    return JSONResponse(
        {
            "cloud": req.cloud,
            "existing_cluster": req.existing_cluster,
            "terraform": {
                "template": terraform_template,
                "files": [{"path": f.path, "content": f.content} for f in terraform_files],
            },
            "helm": {
                "template": helm_template,
                "files": [{"path": f.path, "content": f.content} for f in helm_files],
            },
        }
    )


@app.post("/generate/platform/download")
def platform_download(req: PlatformGenerateRequest):
    terraform_template, helm_template = _resolve_platform_templates(req)

    combined: list[GeneratedFile] = []
    if terraform_template:
        terraform_files = _generate_or_404(
            "terraform", GenerationRequest(template=terraform_template, context=req.terraform_context)
        )
        combined.extend(_prefix_files(terraform_files, "terraform"))

    helm_files = _generate_or_404("helm", GenerationRequest(template=helm_template, context=req.helm_context))
    combined.extend(_prefix_files(helm_files, "helm"))

    blob = to_zip(combined)

    suffix = "workload" if req.existing_cluster else "platform"
    return StreamingResponse(
        iter([blob]),
        media_type="application/zip",
        headers={"Content-Disposition": f"attachment; filename={suffix}-{req.cloud}.zip"},
    )
