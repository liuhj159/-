from __future__ import annotations

import json
import sys
import urllib.parse
from pathlib import Path

from sync_feishu_bitable import ENV_PATH, FEISHU_BASE, get_json, get_tenant_access_token, load_dotenv
from write_feishu_bitable import request_json, writable_target_allowed


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "outputs" / "feishu_quote_ledger_setup"
APP_TOKEN = "HJRKbwEsiaIXlCstXxjcBW5dnNY"
TABLE_ID = "tblBej3wwa6dk5ed"


TARGET_VIEW_NAMES = [
    "全部报价台账",
    "按业务员查看",
    "按报价日期查看",
    "待复核报价",
]


def views_url(view_id: str | None = None) -> str:
    base = f"{FEISHU_BASE}/bitable/v1/apps/{urllib.parse.quote(APP_TOKEN)}/tables/{urllib.parse.quote(TABLE_ID)}/views"
    if view_id:
        return f"{base}/{urllib.parse.quote(view_id)}"
    return base


def list_views(token: str) -> list[dict[str, object]]:
    response = get_json(f"{views_url()}?page_size=100", token)
    if response.get("code") != 0:
        raise RuntimeError(f"list views failed: code={response.get('code')} msg={response.get('msg')}")
    return list((response.get("data") or {}).get("items") or [])


def rename_view(token: str, view_id: str, name: str) -> dict[str, object]:
    response = request_json("PATCH", views_url(view_id), {"view_name": name}, token)
    if response.get("code") != 0:
        response = request_json("PUT", views_url(view_id), {"view_name": name}, token)
    if response.get("code") != 0:
        raise RuntimeError(f"rename view failed: view_id={view_id} code={response.get('code')} msg={response.get('msg')}")
    return response


def create_view(token: str, name: str) -> dict[str, object]:
    response = request_json("POST", views_url(), {"view_name": name, "view_type": "grid"}, token)
    if response.get("code") not in (0, 1254020):
        raise RuntimeError(f"create view failed: {name} code={response.get('code')} msg={response.get('msg')}")
    return response


def main() -> None:
    dotenv = load_dotenv(ENV_PATH)
    allowed, blockers = writable_target_allowed(dotenv, APP_TOKEN, TABLE_ID)
    print(f"writable_target_allowed={allowed}")
    for blocker in blockers:
        print(blocker)
    if not allowed:
        print("status=blocked")
        return

    token = get_tenant_access_token(dotenv)
    before = list_views(token)
    changes: list[dict[str, str]] = []

    for index, name in enumerate(TARGET_VIEW_NAMES):
        views = list_views(token)
        existing = next((view for view in views if view.get("view_name") == name), None)
        if existing:
            changes.append({"action": "skip_existing", "view_name": name})
            continue
        if index < len(views):
            view_id = str(views[index]["view_id"])
            old_name = str(views[index]["view_name"])
            rename_view(token, view_id, name)
            changes.append({"action": "rename_view", "from": old_name, "to": name, "view_id": view_id})
        else:
            create_view(token, name)
            changes.append({"action": "create_view", "view_name": name})

    after = list_views(token)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "view_setup_changes.json").write_text(json.dumps(changes, ensure_ascii=False, indent=2), encoding="utf-8-sig")
    (OUT_DIR / "views_after.json").write_text(json.dumps(after, ensure_ascii=False, indent=2), encoding="utf-8-sig")
    print("status=views_ready")
    print(f"views_before={len(before)}")
    print(f"views_after={len(after)}")
    print(f"changes={OUT_DIR / 'view_setup_changes.json'}")
    print(f"views_after_path={OUT_DIR / 'views_after.json'}")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print("status=error", file=sys.stderr)
        print(str(exc), file=sys.stderr)
        sys.exit(1)
