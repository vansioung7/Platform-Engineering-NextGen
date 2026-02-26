#!/usr/bin/env python3
import argparse
import json
import os
from datetime import datetime, timezone
from pathlib import Path

import requests
from requests.auth import HTTPBasicAuth


START_MARKER = "<!-- AUTO-GENERATED-ARCH-DIAGRAMS-START -->"
END_MARKER = "<!-- AUTO-GENERATED-ARCH-DIAGRAMS-END -->"


def load_env_file(path: Path) -> dict[str, str]:
    env: dict[str, str] = {}
    if not path.exists():
        return env
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        env[key.strip()] = value.strip().strip('"').strip("'")
    return env


def get_env_val(env: dict[str, str], *keys: str) -> str:
    for k in keys:
        if k in os.environ and os.environ[k]:
            return os.environ[k]
        if k in env and env[k]:
            return env[k]
    return ""


def confluence_session(base_url: str, email: str, token: str) -> requests.Session:
    s = requests.Session()
    s.auth = HTTPBasicAuth(email, token)
    s.headers.update({"Accept": "application/json"})
    s.base_url = base_url.rstrip("/")
    return s


def upload_attachment(sess: requests.Session, page_id: str, file_path: Path) -> None:
    list_url = f"{sess.base_url}/wiki/rest/api/content/{page_id}/child/attachment"
    q = sess.get(list_url, params={"filename": file_path.name}, timeout=30)
    q.raise_for_status()
    results = q.json().get("results", [])
    headers = {"X-Atlassian-Token": "no-check"}
    files = {"file": (file_path.name, file_path.read_bytes(), "image/png")}

    if results:
        att_id = results[0]["id"]
        up_url = f"{sess.base_url}/wiki/rest/api/content/{page_id}/child/attachment/{att_id}/data"
        r = sess.post(up_url, headers=headers, files=files, timeout=60)
        r.raise_for_status()
    else:
        r = sess.post(list_url, headers=headers, files=files, timeout=60)
        r.raise_for_status()


def build_diagram_block(system_png: str, sequence_png: str) -> str:
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    return (
        f"{START_MARKER}"
        "<h2>Platform Governance Architecture Diagrams</h2>"
        f"<p>Auto-updated: {now}</p>"
        "<h3>System Architecture</h3>"
        f'<p><ac:image ac:width="1600"><ri:attachment ri:filename="{system_png}" /></ac:image></p>'
        "<h3>Drift Detection and Remediation Sequence</h3>"
        f'<p><ac:image ac:width="1600"><ri:attachment ri:filename="{sequence_png}" /></ac:image></p>'
        f"{END_MARKER}"
    )


def upsert_block(storage: str, block: str) -> str:
    if START_MARKER in storage and END_MARKER in storage:
        start = storage.index(START_MARKER)
        end = storage.index(END_MARKER) + len(END_MARKER)
        return storage[:start] + block + storage[end:]
    return storage + "<hr/>" + block


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--config", default="confluence.env")
    p.add_argument("--page-id", default="12156958")
    p.add_argument("--system-png", default="docs/architecture/generated/system-architecture.png")
    p.add_argument("--sequence-png", default="docs/architecture/generated/drift-sequences.png")
    args = p.parse_args()

    env = load_env_file(Path(args.config))
    base_url = get_env_val(env, "CONFLUENCE_BASE_URL", "CONFLUENCE_URL")
    email = get_env_val(env, "CONFLUENCE_USER_EMAIL", "CONFLUENCE_EMAIL")
    token = get_env_val(env, "CONFLUENCE_API_TOKEN", "CONFLUENCE_TOKEN")
    if not all([base_url, email, token]):
        print("Missing Confluence credentials in env/config.")
        return 2

    system_png = Path(args.system_png)
    sequence_png = Path(args.sequence_png)
    if not system_png.exists() or not sequence_png.exists():
        print("Diagram PNG file(s) missing.")
        return 2

    sess = confluence_session(base_url, email, token)

    upload_attachment(sess, args.page_id, system_png)
    upload_attachment(sess, args.page_id, sequence_png)

    get_url = f"{sess.base_url}/wiki/rest/api/content/{args.page_id}"
    g = sess.get(get_url, params={"expand": "body.storage,version,title,type"}, timeout=30)
    g.raise_for_status()
    page = g.json()

    title = page["title"]
    version = int(page["version"]["number"])
    current_storage = page["body"]["storage"]["value"]
    block = build_diagram_block(system_png.name, sequence_png.name)
    new_storage = upsert_block(current_storage, block)

    update_payload = {
        "id": str(args.page_id),
        "type": page.get("type", "page"),
        "title": title,
        "version": {"number": version + 1},
        "body": {"storage": {"value": new_storage, "representation": "storage"}},
    }
    u = sess.put(get_url, headers={"Content-Type": "application/json"}, data=json.dumps(update_payload), timeout=45)
    u.raise_for_status()
    print(f"Updated page {args.page_id} with embedded architecture diagrams.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

