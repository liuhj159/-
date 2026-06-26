from __future__ import annotations

import json
import sys
import urllib.parse
from pathlib import Path
from typing import Any

from sync_feishu_bitable import ENV_PATH, FEISHU_BASE, get_json, get_tenant_access_token, load_dotenv
from write_feishu_bitable import request_json, writable_target_allowed


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "outputs" / "feishu_quote_ledger_setup"


APP_TOKEN = "HJRKbwEsiaIXlCstXxjcBW5dnNY"
TABLE_ID = "tblBej3wwa6dk5ed"
TABLE_NAME = "工程设计报价"


FIELDS: list[dict[str, Any]] = [
    {"field_name": "项目名称", "type": 1},
    {"field_name": "客户名称", "type": 1},
    {"field_name": "业务员", "type": 1},
    {"field_name": "报价日期", "type": 5, "property": {"date_formatter": "yyyy/MM/dd"}},
    {"field_name": "品牌", "type": 3, "property": {"options": [
        {"name": "日立", "color": 0},
        {"name": "美的", "color": 1},
        {"name": "海尔", "color": 2},
        {"name": "海信", "color": 3},
        {"name": "格力", "color": 4},
        {"name": "多品牌", "color": 5},
    ]}},
    {"field_name": "报价类型", "type": 3, "property": {"options": [
        {"name": "批发", "color": 0},
        {"name": "零售", "color": 1},
        {"name": "批发+零售", "color": 2},
    ]}},
    {"field_name": "模板版本", "type": 1},
    {"field_name": "Excel报价文件链接", "type": 15},
    {"field_name": "报价总额", "type": 2},
    {"field_name": "成本合计", "type": 2},
    {"field_name": "毛利", "type": 2},
    {"field_name": "毛利率", "type": 2},
    {"field_name": "状态", "type": 3, "property": {"options": [
        {"name": "草稿", "color": 0},
        {"name": "待复核", "color": 1},
        {"name": "已报价", "color": 2},
        {"name": "已成交", "color": 3},
        {"name": "作废", "color": 4},
    ]}},
    {"field_name": "库存匹配状态", "type": 3, "property": {"options": [
        {"name": "现货可用", "color": 0},
        {"name": "现货不足", "color": 1},
        {"name": "需采购", "color": 2},
        {"name": "替代待确认", "color": 3},
        {"name": "库存未匹配", "color": 4},
    ]}},
    {"field_name": "复核状态", "type": 3, "property": {"options": [
        {"name": "未复核", "color": 0},
        {"name": "复核中", "color": 1},
        {"name": "已复核", "color": 2},
        {"name": "需修改", "color": 3},
    ]}},
    {"field_name": "模板来源", "type": 1},
    {"field_name": "原始模板路径", "type": 1},
    {"field_name": "备注", "type": 1},
    {"field_name": "创建时间", "type": 1001},
    {"field_name": "最后修改时间", "type": 1002},
]


SEED_RECORD = {
    "报价编号": "QT-TEMPLATE-5BRAND",
    "项目名称": "5品牌报价模板",
    "客户名称": "内部模板",
    "业务员": "模板",
    "品牌": "多品牌",
    "报价类型": "批发+零售",
    "模板版本": "2026-06-06",
    "模板来源": "5品牌精品二手中央空调报价模版汇总；保留日立/美的/海尔/海信/格力报价页和价格数据表公式",
    "原始模板路径": str(ROOT / "5品牌报价模版自动扩展修正版202606_报价公式补齐.xlsx"),
    "状态": "草稿",
    "库存匹配状态": "库存未匹配",
    "复核状态": "未复核",
    "备注": "多维表用于报价台账和筛选；Excel模板继续作为公式计算引擎。",
}


def field_url(field_id: str | None = None) -> str:
    base = f"{FEISHU_BASE}/bitable/v1/apps/{urllib.parse.quote(APP_TOKEN)}/tables/{urllib.parse.quote(TABLE_ID)}/fields"
    if field_id:
        return f"{base}/{urllib.parse.quote(field_id)}"
    return base


def record_url(record_id: str | None = None) -> str:
    base = f"{FEISHU_BASE}/bitable/v1/apps/{urllib.parse.quote(APP_TOKEN)}/tables/{urllib.parse.quote(TABLE_ID)}/records"
    if record_id:
        return f"{base}/{urllib.parse.quote(record_id)}"
    return base


def list_fields(token: str) -> list[dict[str, Any]]:
    response = get_json(f"{field_url()}?page_size=100", token)
    if response.get("code") != 0:
        raise RuntimeError(f"list fields failed: code={response.get('code')} msg={response.get('msg')}")
    return list((response.get("data") or {}).get("items") or [])


def create_field(token: str, spec: dict[str, Any]) -> dict[str, Any]:
    payload = {key: value for key, value in spec.items() if value is not None}
    response = request_json("POST", field_url(), payload, token)
    if response.get("code") != 0:
        raise RuntimeError(f"create field {spec['field_name']} failed: code={response.get('code')} msg={response.get('msg')}")
    return response


def update_field_name(token: str, field_id: str, name: str, field_type: int) -> dict[str, Any]:
    response = request_json("PUT", field_url(field_id), {"field_name": name, "type": field_type}, token)
    if response.get("code") != 0:
        raise RuntimeError(f"rename primary field failed: code={response.get('code')} msg={response.get('msg')}")
    return response


def create_seed_record(token: str, existing_names: set[str]) -> dict[str, Any] | None:
    fields = {key: value for key, value in SEED_RECORD.items() if key in existing_names}
    response = request_json("POST", record_url(), {"fields": fields}, token)
    if response.get("code") != 0:
        raise RuntimeError(f"create seed record failed: code={response.get('code')} msg={response.get('msg')}")
    return response


def main() -> None:
    dotenv = load_dotenv(ENV_PATH)
    allowed, blockers = writable_target_allowed(dotenv, APP_TOKEN, TABLE_ID)
    print(f"target_table={TABLE_NAME}")
    print(f"writable_target_allowed={allowed}")
    for blocker in blockers:
        print(blocker)
    if not allowed:
        print("status=blocked")
        return

    token = get_tenant_access_token(dotenv)
    before = list_fields(token)
    before_names = {field.get("field_name") for field in before}
    changes: list[dict[str, Any]] = []

    primary_text = next((field for field in before if field.get("is_primary") and field.get("field_name") == "文本"), None)
    if primary_text:
        update_field_name(token, str(primary_text["field_id"]), "报价编号", int(primary_text.get("type") or 1))
        changes.append({"action": "rename_primary", "from": "文本", "to": "报价编号"})

    current_names = {field.get("field_name") for field in list_fields(token)}
    for spec in FIELDS:
        if spec["field_name"] in current_names:
            changes.append({"action": "skip_existing", "field_name": spec["field_name"]})
            continue
        create_field(token, spec)
        current_names.add(spec["field_name"])
        changes.append({"action": "create_field", "field_name": spec["field_name"], "type": spec["type"]})

    after = list_fields(token)
    after_names = {str(field.get("field_name")) for field in after}
    create_seed_record(token, after_names)
    changes.append({"action": "create_seed_record", "报价编号": SEED_RECORD["报价编号"]})

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "setup_changes.json").write_text(json.dumps(changes, ensure_ascii=False, indent=2), encoding="utf-8-sig")
    (OUT_DIR / "fields_after.json").write_text(json.dumps(after, ensure_ascii=False, indent=2), encoding="utf-8-sig")

    print("status=created")
    print(f"fields_before={len(before)}")
    print(f"fields_after={len(after)}")
    print(f"changes={OUT_DIR / 'setup_changes.json'}")
    print(f"fields_after_path={OUT_DIR / 'fields_after.json'}")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print("status=error", file=sys.stderr)
        print(str(exc), file=sys.stderr)
        sys.exit(1)
