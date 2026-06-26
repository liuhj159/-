from __future__ import annotations

import argparse
import csv
import hashlib
import json
import shutil
from datetime import datetime
from pathlib import Path


DRAWING_EXTS = {".zip", ".ifc", ".rfa", ".rvt", ".dwg", ".dxf", ".gac"}
CATALOG_ROOT = Path(r"F:\产品知识库\厂家设备图纸\catalog")
TARGET_ROOT = Path(r"F:\产品知识库\厂家设备图纸\manual_import")
SESSION_PATH = CATALOG_ROOT / "login_session.json"
MANIFEST_PATH = CATALOG_ROOT / "manual_download_manifest.csv"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def safe_name(value: str) -> str:
    bad = '<>:"/\\|?*'
    name = "".join("_" if ch in bad or ord(ch) < 32 else ch for ch in value)
    return name.strip(" .") or "downloaded_file"


def unique_path(path: Path) -> Path:
    if not path.exists():
        return path
    for index in range(2, 1000):
        candidate = path.with_name(f"{path.stem}_{index}{path.suffix}")
        if not candidate.exists():
            return candidate
    raise RuntimeError(f"Could not allocate unique path for {path}")


def load_session() -> tuple[Path, datetime]:
    session = json.loads(SESSION_PATH.read_text(encoding="utf-8-sig"))
    downloads_folder = Path(session["downloads_folder"])
    started_at = datetime.fromisoformat(session["started_at"])
    return downloads_folder, started_at


def existing_hashes() -> set[str]:
    if not MANIFEST_PATH.exists():
        return set()
    with MANIFEST_PATH.open("r", encoding="utf-8-sig", newline="") as handle:
        return {row.get("sha256", "") for row in csv.DictReader(handle) if row.get("sha256")}


def append_manifest(rows: list[dict[str, str]]) -> None:
    fieldnames = [
        "brand",
        "source_name",
        "source_url",
        "original_download_path",
        "local_path",
        "file_ext",
        "bytes",
        "sha256",
        "imported_at",
        "notes",
    ]
    MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)
    exists = MANIFEST_PATH.exists()
    with MANIFEST_PATH.open("a", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        if not exists:
            writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--brand", required=True, help="Brand name, e.g. Midea")
    parser.add_argument("--source-name", default="", help="Source name for manifest")
    parser.add_argument("--source-url", default="", help="Source URL for manifest")
    parser.add_argument("--since", default="", help="ISO timestamp override")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    downloads_folder, started_at = load_session()
    if args.since:
        started_at = datetime.fromisoformat(args.since)

    imported_hashes = existing_hashes()
    brand_folder = TARGET_ROOT / safe_name(args.brand)
    candidates = [
        item
        for item in downloads_folder.iterdir()
        if item.is_file()
        and item.suffix.lower() in DRAWING_EXTS
        and datetime.fromtimestamp(item.stat().st_mtime) >= started_at
    ]

    rows: list[dict[str, str]] = []
    for source in sorted(candidates, key=lambda p: p.stat().st_mtime):
        checksum = sha256_file(source)
        if checksum in imported_hashes:
            continue
        target = unique_path(brand_folder / safe_name(source.name))
        if not args.dry_run:
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
        rows.append(
            {
                "brand": args.brand,
                "source_name": args.source_name,
                "source_url": args.source_url,
                "original_download_path": str(source),
                "local_path": str(target),
                "file_ext": source.suffix.lower().lstrip("."),
                "bytes": str(source.stat().st_size),
                "sha256": checksum,
                "imported_at": datetime.now().isoformat(timespec="seconds"),
                "notes": "manual browser download copied from Downloads",
            }
        )

    if rows and not args.dry_run:
        append_manifest(rows)

    print(f"found={len(candidates)} new={len(rows)} target={brand_folder}")
    for row in rows[:20]:
        print(row["local_path"])
    if len(rows) > 20:
        print(f"... {len(rows) - 20} more")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
