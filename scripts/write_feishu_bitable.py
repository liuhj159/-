from __future__ import annotations

import argparse
import csv
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
ENV_PATH = ROOT / ".env"
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


def request_json(method: str, url: str, payload: dict[str, object] | None = None, token: str | None = None) -> dict[str, Any]:
    data = None if payload is None else json.dumps(payload, ensure_ascii=False).encode("utf-8")
    headers = {"Content-Type": "application/json; charset=utf-8"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = urllib.request.Request(url, data=data, headers=headers, method=method)
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
    response = request_json(
        "POST",
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


def parse_value(value: str, auto_type: bool) -> Any:
    value = value.strip()
    if not auto_type:
        return value
    if value == "":
        return ""
    lowered = value.lower()
    if lowered == "true":
        return True
    if lowered == "false":
        return False
    try:
        if "." not in value:
            return int(value)
        return float(value)
    except ValueError:
        return value


def read_csv_rows(path: Path, fields: list[str], skip_internal: bool, auto_type: bool) -> list[dict[str, Any]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        rows: list[dict[str, Any]] = []
        selected = fields or list(reader.fieldnames or [])
        for raw in reader:
            row: dict[str, Any] = {}
            for name in selected:
                if skip_internal and name.startswith("_"):
                    continue
                if name in raw:
                    row[name] = parse_value(raw[name], auto_type)
            rows.append(row)
        return rows


def create_record(token: str, app_token: str, table_id: str, fields: dict[str, Any]) -> dict[str, Any]:
    url = f"{FEISHU_BASE}/bitable/v1/apps/{urllib.parse.quote(app_token)}/tables/{urllib.parse.quote(table_id)}/records"
    return request_json("POST", url, {"fields": fields}, token)


def update_record(token: str, app_token: str, table_id: str, record_id: str, fields: dict[str, Any]) -> dict[str, Any]:
    url = (
        f"{FEISHU_BASE}/bitable/v1/apps/{urllib.parse.quote(app_token)}/"
        f"tables/{urllib.parse.quote(table_id)}/records/{urllib.parse.quote(record_id)}"
    )
    return request_json("PUT", url, {"fields": fields}, token)


def writable_target_allowed(dotenv: dict[str, str], app_token: str, table_id: str) -> tuple[bool, list[str]]:
    expected_app_token = cfg("FEISHU_WRITABLE_APP_TOKEN", dotenv)
    expected_table_id = cfg("FEISHU_WRITABLE_TABLE_ID", dotenv)
    reasons: list[str] = []
    if not expected_app_token:
        reasons.append("missing: FEISHU_WRITABLE_APP_TOKEN")
    if not expected_table_id:
        reasons.append("missing: FEISHU_WRITABLE_TABLE_ID")
    if expected_app_token and app_token != expected_app_token:
        reasons.append("blocked: app_token is not in writable allowlist")
    if expected_table_id and table_id != expected_table_id:
        reasons.append("blocked: table_id is not in writable allowlist")
    return not reasons, reasons


def main() -> None:
    parser = argparse.ArgumentParser(description="Upload or write CSV rows back to a Feishu Bitable table.")
    parser.add_argument("--csv", type=Path, required=True, help="CSV file to write.")
    parser.add_argument("--url", help="Feishu Bitable URL. If omitted, uses FEISHU_APP_TOKEN and FEISHU_INVENTORY_TABLE_ID.")
    parser.add_argument("--app-token", help="Bitable app_token override.")
    parser.add_argument("--table-id", help="Bitable table_id override.")
    parser.add_argument("--mode", choices=["create", "update"], required=True)
    parser.add_argument("--record-id-field", default="_record_id", help="CSV field holding Feishu record_id for update mode.")
    parser.add_argument("--fields", nargs="*", default=[], help="Field names to write. Default writes all CSV columns except internal fields.")
    parser.add_argument("--auto-type", action="store_true", help="Convert numeric and boolean-looking CSV values before writing.")
    parser.add_argument("--execute", action="store_true", help="Actually write to Feishu. Default is dry-run.")
    args = parser.parse_args()

    dotenv = load_dotenv(ENV_PATH)
    parsed = parse_bitable_url(args.url) if args.url else {"app_token": "", "table_id": "", "view_id": ""}
    app_token = args.app_token or parsed["app_token"] or cfg("FEISHU_APP_TOKEN", dotenv)
    table_id = args.table_id or parsed["table_id"] or cfg("FEISHU_INVENTORY_TABLE_ID", dotenv)
    upload_allowed = cfg("ALLOW_EXTERNAL_UPLOAD", dotenv).lower() == "true"
    target_allowed, target_blockers = writable_target_allowed(dotenv, app_token, table_id)
    missing_config = [
        key
        for key in ("FEISHU_APP_ID", "FEISHU_APP_SECRET")
        if not cfg(key, dotenv) and not cfg("FEISHU_TENANT_ACCESS_TOKEN", dotenv)
    ]
    missing_source = []
    if not app_token:
        missing_source.append("app_token")
    if not table_id:
        missing_source.append("table_id")
    if not args.csv.exists():
        missing_source.append("csv")

    print(f"env_file={'present' if ENV_PATH.exists() else 'missing'}")
    print(f"csv={args.csv}")
    print(f"csv_exists={args.csv.exists()}")
    print(f"mode={args.mode}")
    print(f"app_token_configured={bool(app_token)}")
    print(f"table_id_configured={bool(table_id)}")
    print(f"writable_allowlist_configured={bool(cfg('FEISHU_WRITABLE_APP_TOKEN', dotenv) and cfg('FEISHU_WRITABLE_TABLE_ID', dotenv))}")
    print(f"writable_target_allowed={target_allowed}")
    for blocker in target_blockers:
        print(blocker)
    print(f"external_upload_allowed={upload_allowed}")
    print(f"execute={args.execute}")
    print(f"missing_config_count={len(missing_config)}")
    for key in missing_config:
        print(f"missing: {key}")
    print(f"missing_source_count={len(missing_source)}")
    for key in missing_source:
        print(f"missing_source: {key}")

    if missing_config or missing_source:
        print("status=dry_run_or_blocked")
        return

    rows = read_csv_rows(args.csv, args.fields, skip_internal=True, auto_type=args.auto_type)
    print(f"rows_to_write={len(rows)}")
    if args.mode == "update":
        with args.csv.open("r", encoding="utf-8-sig", newline="") as f:
            missing_record_ids = sum(1 for row in csv.DictReader(f) if not row.get(args.record_id_field, "").strip())
        print(f"missing_record_ids={missing_record_ids}")
        if missing_record_ids:
            print("status=dry_run_or_blocked")
            return

    if not target_allowed or not upload_allowed or not args.execute:
        print("status=dry_run_or_blocked")
        return

    token = get_tenant_access_token(dotenv)
    ok = 0
    failures: list[dict[str, object]] = []
    if args.mode == "create":
        for index, fields in enumerate(rows, start=1):
            response = create_record(token, app_token, table_id, fields)
            if response.get("code") == 0:
                ok += 1
            else:
                failures.append({"row": index, "code": response.get("code"), "msg": response.get("msg")})
    else:
        with args.csv.open("r", encoding="utf-8-sig", newline="") as f:
            raw_rows = list(csv.DictReader(f))
        for index, fields in enumerate(rows, start=1):
            record_id = raw_rows[index - 1].get(args.record_id_field, "").strip()
            response = update_record(token, app_token, table_id, record_id, fields)
            if response.get("code") == 0:
                ok += 1
            else:
                failures.append({"row": index, "record_id": record_id, "code": response.get("code"), "msg": response.get("msg")})

    print("status=written" if not failures else "status=partial_error")
    print(f"written={ok}")
    print(f"failures={len(failures)}")
    if failures:
        print(json.dumps(failures[:20], ensure_ascii=False, indent=2))


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print("status=error", file=sys.stderr)
        print(str(exc), file=sys.stderr)
        sys.exit(1)
