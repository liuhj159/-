from __future__ import annotations

import argparse
import json
import mimetypes
import os
import secrets
import sys
import urllib.error
import urllib.request
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ENV_PATH = ROOT / ".env"
DEFAULT_FILE = ROOT / "outputs" / "feishu_quote_template_import" / "5_brand_quote_template_feishu_import.xlsx"

FEISHU_BASE = "https://open.feishu.cn/open-apis"


def load_dotenv(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not path.exists():
        return values
    for line in path.read_text(encoding="utf-8-sig").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        values[key.strip()] = value.strip().strip('"').strip("'")
    return values


def cfg(key: str, dotenv: dict[str, str]) -> str:
    return os.environ.get(key) or dotenv.get(key, "")


def require_config(dotenv: dict[str, str]) -> list[str]:
    required = ["FEISHU_APP_ID", "FEISHU_APP_SECRET", "FEISHU_PROJECT_FOLDER_TOKEN"]
    return [key for key in required if not cfg(key, dotenv)]


def post_json(url: str, payload: dict[str, object], token: str | None = None) -> dict[str, object]:
    data = json.dumps(payload).encode("utf-8")
    headers = {"Content-Type": "application/json; charset=utf-8"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = urllib.request.Request(url, data=data, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"HTTP {e.code}: {body}") from e


def get_tenant_access_token(dotenv: dict[str, str]) -> str:
    existing = cfg("FEISHU_TENANT_ACCESS_TOKEN", dotenv)
    if existing:
        return existing
    response = post_json(
        f"{FEISHU_BASE}/auth/v3/tenant_access_token/internal",
        {
            "app_id": cfg("FEISHU_APP_ID", dotenv),
            "app_secret": cfg("FEISHU_APP_SECRET", dotenv),
        },
    )
    if response.get("code") != 0:
        raise RuntimeError(f"tenant_access_token failed: code={response.get('code')} msg={response.get('msg')}")
    token = response.get("tenant_access_token")
    if not isinstance(token, str) or not token:
        raise RuntimeError("tenant_access_token missing in Feishu response")
    return token


def multipart_body(fields: dict[str, str], file_field: str, file_path: Path) -> tuple[bytes, str]:
    boundary = "----codex-feishu-" + secrets.token_hex(12)
    mime_type = mimetypes.guess_type(file_path.name)[0] or "application/octet-stream"
    chunks: list[bytes] = []
    for key, value in fields.items():
        chunks.append(f"--{boundary}\r\n".encode("utf-8"))
        chunks.append(f'Content-Disposition: form-data; name="{key}"\r\n\r\n'.encode("utf-8"))
        chunks.append(str(value).encode("utf-8"))
        chunks.append(b"\r\n")
    chunks.append(f"--{boundary}\r\n".encode("utf-8"))
    chunks.append(
        (
            f'Content-Disposition: form-data; name="{file_field}"; filename="{file_path.name}"\r\n'
            f"Content-Type: {mime_type}\r\n\r\n"
        ).encode("utf-8")
    )
    chunks.append(file_path.read_bytes())
    chunks.append(b"\r\n")
    chunks.append(f"--{boundary}--\r\n".encode("utf-8"))
    return b"".join(chunks), boundary


def upload_file(token: str, folder_token: str, file_path: Path) -> dict[str, object]:
    fields = {
        "file_name": file_path.name,
        "parent_type": "explorer",
        "parent_node": folder_token,
        "size": str(file_path.stat().st_size),
    }
    body, boundary = multipart_body(fields, "file", file_path)
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": f"multipart/form-data; boundary={boundary}",
    }
    request = urllib.request.Request(
        f"{FEISHU_BASE}/drive/v1/files/upload_all",
        data=body,
        headers=headers,
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=180) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body_text = e.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"HTTP {e.code}: {body_text}") from e


def main() -> None:
    parser = argparse.ArgumentParser(description="Upload prepared quote template to Feishu Drive.")
    parser.add_argument("--file", type=Path, default=DEFAULT_FILE)
    parser.add_argument("--execute", action="store_true", help="Actually upload. Default is dry-run.")
    args = parser.parse_args()

    dotenv = load_dotenv(ENV_PATH)
    missing = require_config(dotenv)
    upload_allowed = cfg("ALLOW_EXTERNAL_UPLOAD", dotenv).lower() == "true"

    print(f"env_file={'present' if ENV_PATH.exists() else 'missing'}")
    print(f"file={args.file}")
    print(f"file_exists={args.file.exists()}")
    if args.file.exists():
        print(f"file_size={args.file.stat().st_size}")
    print(f"missing_config_count={len(missing)}")
    for key in missing:
        print(f"missing: {key}")
    print(f"external_upload_allowed={upload_allowed}")
    print(f"execute={args.execute}")

    if missing or not args.file.exists() or not upload_allowed or not args.execute:
        print("status=dry_run_or_blocked")
        return

    token = get_tenant_access_token(dotenv)
    response = upload_file(token, cfg("FEISHU_PROJECT_FOLDER_TOKEN", dotenv), args.file)
    safe_response = {
        "code": response.get("code"),
        "msg": response.get("msg"),
        "data": response.get("data"),
    }
    print("status=uploaded")
    print(json.dumps(safe_response, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"status=error", file=sys.stderr)
        print(str(exc), file=sys.stderr)
        sys.exit(1)
