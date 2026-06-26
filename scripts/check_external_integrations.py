from __future__ import annotations

import os
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ENV_PATH = ROOT / ".env"

REQUIRED_GROUPS = {
    "feishu": [
        "FEISHU_APP_ID",
        "FEISHU_APP_SECRET",
        "FEISHU_APP_TOKEN",
        "FEISHU_INVENTORY_TABLE_ID",
        "FEISHU_WRITABLE_APP_TOKEN",
        "FEISHU_WRITABLE_TABLE_ID",
        "FEISHU_QUOTE_TEMPLATE_FILE_TOKEN",
        "FEISHU_PROJECT_FOLDER_TOKEN",
    ],
    "qwen": [
        "DASHSCOPE_API_KEY",
        "QWEN_MODEL",
    ],
    "safety": [
        "ALLOW_EXTERNAL_UPLOAD",
        "ALLOW_LLM_DOCUMENT_ANALYSIS",
    ],
}


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


def value_for(key: str, dotenv: dict[str, str]) -> str:
    return os.environ.get(key) or dotenv.get(key, "")


def main() -> None:
    dotenv = load_dotenv(ENV_PATH)
    print(f"env_file={'present' if ENV_PATH.exists() else 'missing'}")
    for group, keys in REQUIRED_GROUPS.items():
        configured = []
        missing = []
        for key in keys:
            if value_for(key, dotenv):
                configured.append(key)
            else:
                missing.append(key)
        print(f"[{group}] configured={len(configured)} missing={len(missing)}")
        for key in missing:
            print(f"  missing: {key}")

    upload_allowed = value_for("ALLOW_EXTERNAL_UPLOAD", dotenv).lower() == "true"
    llm_allowed = value_for("ALLOW_LLM_DOCUMENT_ANALYSIS", dotenv).lower() == "true"
    print(f"external_upload_allowed={upload_allowed}")
    print(f"llm_document_analysis_allowed={llm_allowed}")


if __name__ == "__main__":
    main()
