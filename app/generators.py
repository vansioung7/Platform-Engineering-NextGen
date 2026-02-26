from __future__ import annotations

from dataclasses import dataclass
from io import BytesIO
from pathlib import Path
import zipfile

from jinja2 import Environment, FileSystemLoader, StrictUndefined


@dataclass
class GeneratedFile:
    path: str
    content: str


class TemplateGenerator:
    def __init__(self, base_dir: Path) -> None:
        self.base_dir = base_dir
        self.jinja = Environment(
            loader=FileSystemLoader(str(base_dir)),
            autoescape=False,
            trim_blocks=True,
            lstrip_blocks=True,
            undefined=StrictUndefined,
        )

    def generate(self, template_type: str, template_name: str, context: dict) -> list[GeneratedFile]:
        template_root = self.base_dir / template_type / template_name
        if not template_root.exists() or not template_root.is_dir():
            raise FileNotFoundError(f"Template not found: {template_type}/{template_name}")

        generated: list[GeneratedFile] = []
        for file_path in sorted(template_root.rglob("*")):
            if file_path.is_dir():
                continue

            rel = file_path.relative_to(template_root)
            source = file_path.read_text(encoding="utf-8")
            if file_path.suffix == ".j2":
                rel_out = str(rel.with_suffix(""))
                template_ref = str(file_path.relative_to(self.base_dir)).replace("\\", "/")
                rendered = self.jinja.get_template(template_ref).render(**context)
                generated.append(GeneratedFile(path=rel_out.replace("\\", "/"), content=rendered + "\n"))
            else:
                generated.append(GeneratedFile(path=str(rel).replace("\\", "/"), content=source))

        return generated


def to_zip(files: list[GeneratedFile]) -> bytes:
    buffer = BytesIO()
    with zipfile.ZipFile(buffer, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
        for item in files:
            zf.writestr(item.path, item.content)
    return buffer.getvalue()
