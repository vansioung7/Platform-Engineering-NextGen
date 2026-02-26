from typing import Any, Literal

from pydantic import BaseModel, Field


class GenerationRequest(BaseModel):
    template: str = Field(..., description="Template name under templates/<type>/<template>")
    context: dict[str, Any] = Field(default_factory=dict)


class PlatformGenerateRequest(BaseModel):
    cloud: Literal["aws", "azure", "gcp"] = Field(..., description="Target cloud provider")
    existing_cluster: bool = Field(
        default=False,
        description="If true, skip Terraform cluster generation and generate workload artifacts only",
    )
    terraform_context: dict[str, Any] = Field(default_factory=dict)
    helm_context: dict[str, Any] = Field(default_factory=dict)
    terraform_template: str | None = Field(
        default=None, description="Optional Terraform template override"
    )
    helm_template: str | None = Field(default=None, description="Optional Helm template override")
