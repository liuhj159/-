from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
ENV_PATH = ROOT / ".env"
OUT_DIR = ROOT / "outputs" / "feishu_inventory_sync"
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


def parse_bitable_url(url: str) -> dict[str, str]:
    parsed = urllib.parse.urlparse(url)
    parts = [part for part in parsed.path.split("/") if part]
    app_token = ""
    if "base" in parts:
        base_index = parts.index("base")
        if len(parts) > base_index + 1:
            app_token = parts[base_index + 1]
    query = urllib.parse.parse_qs(parsed.query)
    return {
        "app_token": app_token,
        "table_id": query.get("table", [""])[0],
        "view_id": query.get("view", [""])[0],
    }


def post_json(url: str, payload: dict[str, object], token: str | None = None) -> dict[str, Any]:
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
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


def get_json(url: str, token: str) -> dict[str, Any]:
    headers = {"Authorization": f"Bearer {token}"}
    request = urllib.request.Request(url, headers=headers, method="GET")
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


def safe_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, (str, int, float, bool)):
        return str(value)
    if isinstance(value, list):
        return "; ".join(safe_text(item) for item in value if safe_text(item))
    if isinstance(value, dict):
        for key in ("text", "name", "en_name", "email", "phone", "link", "url", "value"):
            if key in value and value[key] not in (None, ""):
                return safe_text(value[key])
        return json.dumps(value, ensure_ascii=False, sort_keys=True)
    return str(value)


def fetch_records(token: str, app_token: str, table_id: str, view_id: str, page_size: int) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    page_token = ""
    while True:
        params = {"page_size": str(page_size)}
        if view_id:
            params["view_id"] = view_id
        if page_token:
            params["page_token"] = page_token
        url = (
            f"{FEISHU_BASE}/bitable/v1/apps/{urllib.parse.quote(app_token)}/"
            f"tables/{urllib.parse.quote(table_id)}/records?"
            f"{urllib.parse.urlencode(params)}"
        )
        response = get_json(url, token)
        if response.get("code") != 0:
            raise RuntimeError(f"records fetch failed: code={response.get('code')} msg={response.get('msg')}")
        data = response.get("data") or {}
        items = data.get("items") or []
        if not isinstance(items, list):
            raise RuntimeError("records response data.items is not a list")
        records.extend(items)
        if not data.get("has_more"):
            break
        page_token = str(data.get("page_token") or "")
        if not page_token:
            raise RuntimeError("Feishu response has_more=true but page_token is missing")
    return records


def flatten_records(records: list[dict[str, Any]]) -> tuple[list[str], list[dict[str, str]]]:
    field_names: list[str] = []
    seen: set[str] = set()
    rows: list[dict[str, str]] = []
    for record in records:
        fields = record.get("fields") or {}
        if not isinstance(fields, dict):
            fields = {}
        row: dict[str, str] = {
            "_record_id": safe_text(record.get("record_id")),
            "_created_time": safe_text(record.get("created_time")),
            "_last_modified_time": safe_text(record.get("last_modified_time")),
        }
        for name, value in fields.items():
            if name not in seen:
                seen.add(name)
                field_names.append(name)
            row[name] = safe_text(value)
        rows.append(row)
    columns = ["_record_id", "_created_time", "_last_modified_time", *field_names]
    return columns, rows


def write_outputs(records: list[dict[str, Any]], source: dict[str, str], dotenv: dict[str, str]) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    fetched_at = datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")
    columns, rows = flatten_records(records)

    raw_path = OUT_DIR / "feishu_inventory_records.json"
    csv_path = OUT_DIR / "feishu_inventory_snapshot.csv"
    manifest_path = OUT_DIR / "sync_manifest.json"

    raw_payload = {
        "fetched_at": fetched_at,
        "source": source,
        "record_count": len(records),
        "records": records,
    }
    raw_path.write_text(json.dumps(raw_payload, ensure_ascii=False, indent=2), encoding="utf-8-sig")

    with csv_path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)

    digest = hashlib.sha256(csv_path.read_bytes()).hexdigest()
    manifest = {
        "fetched_at": fetched_at,
        "source_type": "feishu_bitable_api",
        "app_token": source["app_token"],
        "table_id": source["table_id"],
        "view_id": source["view_id"],
        "record_count": len(records),
        "csv_path": str(csv_path),
        "json_path": str(raw_path),
        "csv_sha256": digest,
        "credentials": {
            "FEISHU_APP_ID": bool(cfg("FEISHU_APP_ID", dotenv)),
            "FEISHU_APP_SECRET": bool(cfg("FEISHU_APP_SECRET", dotenv)),
            "FEISHU_TENANT_ACCESS_TOKEN": bool(cfg("FEISHU_TENANT_ACCESS_TOKEN", dotenv)),
        },
    }
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8-sig")

    print(f"status=synced")
    print(f"records={len(records)}")
    print(f"csv={csv_path}")
    print(f"json={raw_path}")
    print(f"manifest={manifest_path}")
    print(f"csv_sha256={digest}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Read Feishu Bitable records into a local read-only snapshot.")
    parser.add_argument("--url", help="Feishu Bitable URL. If omitted, uses FEISHU_APP_TOKEN and FEISHU_INVENTORY_TABLE_ID.")
    parser.add_argument("--app-token", help="Bitable app_token override.")
    parser.add_argument("--table-id", help="Bitable table_id override.")
    parser.add_argument("--view-id", help="Bitable view_id override.")
    parser.add_argument("--page-size", type=int, default=500, help="Records per request, default 500.")
    parser.add_argument("--dry-run", action="store_true", help="Only parse config and check required credentials.")
    args = parser.parse_args()

    dotenv = load_dotenv(ENV_PATH)
    parsed = parse_bitable_url(args.url) if args.url else {"app_token": "", "table_id": "", "view_id": ""}
    source = {
        "app_token": args.app_token or parsed["app_token"] or cfg("FEISHU_APP_TOKEN", dotenv),
        "table_id": args.table_id or parsed["table_id"] or cfg("FEISHU_INVENTORY_TABLE_ID", dotenv),
        "view_id": args.view_id or parsed["view_id"] or cfg("FEISHU_INVENTORY_VIEW_ID", dotenv),
    }
    missing_config = [
        key
        for key in ("FEISHU_APP_ID", "FEISHU_APP_SECRET")
        if not cfg(key, dotenv) and not cfg("FEISHU_TENANT_ACCESS_TOKEN", dotenv)
    ]
    missing_source = [key for key in ("app_token", "table_id") if not source[key]]

    print(f"env_file={'present' if ENV_PATH.exists() else 'missing'}")
    print(f"app_token_configured={bool(source['app_token'])}")
    print(f"table_id_configured={bool(source['table_id'])}")
    print(f"view_id_configured={bool(source['view_id'])}")
    print(f"missing_config_count={len(missing_config)}")
    for key in missing_config:
        print(f"missing: {key}")
    print(f"missing_source_count={len(missing_source)}")
    for key in missing_source:
        print(f"missing_source: {key}")

    if args.dry_run or missing_config or missing_source:
        print("status=dry_run_or_blocked")
        return

    token = get_tenant_access_token(dotenv)
    records = fetch_records(token, source["app_token"], source["table_id"], source["view_id"], args.page_size)
    write_outputs(records, source, dotenv)


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print("status=error", file=sys.stderr)
        print(str(exc), file=sys.stderr)
        sys.exit(1)
