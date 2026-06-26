from __future__ import annotations

import csv
import hashlib
import html.parser
import os
import re
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable
from urllib.parse import unquote, urljoin, urlparse
from urllib.request import Request, urlopen


ROOT = Path(r"F:\产品知识库\厂家设备图纸")
FILES_ROOT = ROOT / "official_bim_cad"
CATALOG_ROOT = ROOT / "catalog"

DRAWING_EXTS = {".zip", ".ifc", ".rfa", ".rvt", ".dwg", ".dxf"}
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0 Safari/537.36"
)


@dataclass(frozen=True)
class SourcePage:
    brand: str
    source_name: str
    url: str
    folder: str
    note: str = ""


@dataclass
class LinkRecord:
    brand: str
    source_name: str
    source_url: str
    link_text: str
    file_url: str
    local_path: Path
    ext: str
    note: str


SOURCE_PAGES: list[SourcePage] = [
    SourcePage(
        brand="Haier",
        source_name="Haier HVAC Europe BIM Downloads",
        url="https://haierhvac.eu/products/bim-downloads",
        folder="Haier_HVAC_EU_BIM",
        note="Official Haier HVAC Europe BIM page with Revit ZIP and IFC files.",
    ),
    SourcePage(
        brand="Carrier",
        source_name="Carrier Ductless Systems Revit Templates",
        url="https://www.carrier.com/commercial/en/us/software/revit-3d-templates/ductless-systems/",
        folder="Carrier_US_Revit_Ductless",
        note="Official Carrier Commercial page; files hosted by Carrier sharedocs.",
    ),
    SourcePage(
        brand="Carrier",
        source_name="Carrier and Toshiba Carrier VRF Revit Templates",
        url="https://www.carrier.com/commercial/en/us/software/revit-3d-templates/vrf/",
        folder="Carrier_US_Revit_VRF",
        note="Official Carrier Commercial VRF page; includes Carrier VRF and Toshiba Carrier VRF.",
    ),
    SourcePage(
        brand="Trane",
        source_name="Trane Thermal Energy Storage BIM",
        url="https://www.trane.com/commercial/north-america/us/en/support/resources/bim-and-selection-tools.html",
        folder="Trane_US_Thermal_Energy_Storage_Revit",
        note="Official Trane BIM and Selection Tools page; direct RFA downloads for thermal energy storage tanks.",
    ),
]

BLOCKED_SOURCES = [
    {
        "brand": "Daikin",
        "source_name": "Daikin China BIM Download",
        "url": "https://www.daikin-china.com.cn/ca/BIMDownload",
        "status": "manual_or_dynamic",
        "reason": "Official page is available, but direct file links are not present in static HTML.",
        "note": "Use as official entry point; manual download or authenticated workflow may be required.",
    },
    {
        "brand": "Daikin",
        "source_name": "Daikin Global BIM Library",
        "url": "https://www.daikin-bim-library.daikin.com/DKG-BIMDOWNLOAD/en",
        "status": "cart_or_login_flow",
        "reason": "Model pages expose Revit version buttons and cart flow, but no stable direct file URL was downloadable anonymously.",
        "note": "The page can be used for model-level dimensions/specs and manual RFA export.",
    },
    {
        "brand": "Midea",
        "source_name": "Midea Goujianwu Revit Library",
        "url": "https://midea.goujianwu.com/",
        "status": "login_quota_required",
        "reason": "Detail pages show RFA models, dimensions and 'immediate download', but also require login/SMS and quota.",
        "note": "Authorized/public catalog; download requires user account action.",
    },
    {
        "brand": "Gree",
        "source_name": "Gree Goujianwu Revit Library",
        "url": "https://gree.goujianwu.com/",
        "status": "login_quota_required",
        "reason": "Detail pages show RFA models and download controls, but download availability is gated by login/quota.",
        "note": "Authorized/public catalog; download requires user account action.",
    },
    {
        "brand": "Mitsubishi Electric",
        "source_name": "Mitsubishi Electric Trane MPro Product Pages",
        "url": "https://www.mitsubishipro.com/products/",
        "status": "javascript_api_needs_followup",
        "reason": "Product pages list CAD/Revit documents in the rendered app, but static fetch only returns the app shell.",
        "note": "Needs browser/API inspection or manual product-level download.",
    },
    {
        "brand": "Samsung",
        "source_name": "Samsung HVAC Technical Documents",
        "url": "https://www.samsunghvac.com/downloads",
        "status": "dynamic_search_needs_followup",
        "reason": "Official document search lists REVIT BIM and DWG results for model queries, but static fetch did not expose direct file URLs.",
        "note": "Use model-level search manually or inspect the site API before importing.",
    },
    {
        "brand": "LG",
        "source_name": "LG HVAC BIM Library",
        "url": "https://lghvac.com/bim-library/",
        "status": "partner_platform",
        "reason": "Official LG page points users to a BIMsmith-hosted BIM library rather than direct files in static HTML.",
        "note": "Treat BIMsmith downloads as partner-platform content and record that source explicitly if imported.",
    },
    {
        "brand": "Panasonic",
        "source_name": "Panasonic North America BIM Library",
        "url": "https://iaq.na.panasonic.com/resources/resource-center/bim-library",
        "status": "partner_platform",
        "reason": "Official Panasonic page describes BIM/Revit downloads, but direct file URLs were not present in static HTML.",
        "note": "Manual/partner-platform download may be required.",
    },
    {
        "brand": "Mitsubishi Heavy Industries",
        "source_name": "MHI Building Information Modelling",
        "url": "https://www.mhi.com/group/maco/building-information-modelling",
        "status": "partner_search_service",
        "reason": "Official MHI page states VRF/RAC/PAC Revit BIM support and uses MEPcontent search service, not direct static links.",
        "note": "Manual/MEPcontent workflow may be required.",
    },
    {
        "brand": "Trane",
        "source_name": "Trane Generated BIM-Revit Request Flow",
        "url": "https://www.trane.com/commercial/north-america/us/en/support/resources/bim-and-selection-tools.html",
        "status": "email_request_flow",
        "reason": "The same official page states many refrigeration/unitary/air-terminal/heating Revit files are generated and emailed after request.",
        "note": "Only direct thermal-energy-storage RFAs are auto-downloaded; generated files require user email/request.",
    },
]


class LinkParser(html.parser.HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.links: list[tuple[str, str]] = []
        self._href_stack: list[str | None] = []
        self._text_stack: list[list[str] | None] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() != "a":
            return
        attr = {name.lower(): value for name, value in attrs}
        href = attr.get("href")
        self._href_stack.append(href)
        self._text_stack.append([])

    def handle_data(self, data: str) -> None:
        if self._text_stack and self._text_stack[-1] is not None:
            self._text_stack[-1].append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() != "a" or not self._href_stack:
            return
        href = self._href_stack.pop()
        text_parts = self._text_stack.pop() or []
        text = " ".join(part.strip() for part in text_parts if part.strip())
        if href:
            self.links.append((href, re.sub(r"\s+", " ", text).strip()))


def fetch_text(url: str) -> str:
    request = Request(url, headers={"User-Agent": USER_AGENT})
    with urlopen(request, timeout=60) as response:
        charset = response.headers.get_content_charset() or "utf-8"
        return response.read().decode(charset, errors="replace")


def ext_from_url(url: str) -> str:
    path = urlparse(url).path
    return Path(unquote(path)).suffix.lower()


def is_drawing_url(url: str) -> bool:
    return ext_from_url(url) in DRAWING_EXTS


def safe_name(value: str, fallback: str) -> str:
    value = unquote(value).strip() or fallback
    value = re.sub(r"[<>:\"/\\|?*\x00-\x1f]", "_", value)
    value = re.sub(r"\s+", " ", value).strip(" .")
    return value[:180] or fallback


def collision_free_path(path: Path, used_paths: set[Path]) -> Path:
    if path not in used_paths:
        used_paths.add(path)
        return path
    stem = path.stem
    suffix = path.suffix
    for index in range(2, 1000):
        candidate = path.with_name(f"{stem}_{index}{suffix}")
        if candidate not in used_paths:
            used_paths.add(candidate)
            return candidate
    raise RuntimeError(f"Could not allocate unique filename for {path}")


def discover_links(source: SourcePage) -> list[LinkRecord]:
    html = fetch_text(source.url)
    parser = LinkParser()
    parser.feed(html)
    records: list[LinkRecord] = []
    seen: set[str] = set()
    used_paths: set[Path] = set()

    for href, text in parser.links:
        absolute_url = urljoin(source.url, href)
        if not is_drawing_url(absolute_url):
            continue
        if absolute_url in seen:
            continue
        seen.add(absolute_url)
        parsed_name = Path(unquote(urlparse(absolute_url).path)).name
        filename = safe_name(parsed_name, f"{source.folder}_{len(records) + 1}{ext_from_url(absolute_url)}")
        local_path = collision_free_path(FILES_ROOT / source.folder / filename, used_paths)
        records.append(
            LinkRecord(
                brand=source.brand,
                source_name=source.source_name,
                source_url=source.url,
                link_text=text,
                file_url=absolute_url,
                local_path=local_path,
                ext=ext_from_url(absolute_url).lstrip("."),
                note=source.note,
            )
        )
    return records


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def download(record: LinkRecord) -> dict[str, str]:
    record.local_path.parent.mkdir(parents=True, exist_ok=True)
    start = time.time()
    status = "downloaded"
    error = ""
    if record.local_path.exists() and record.local_path.stat().st_size > 0:
        status = "exists"
    else:
        try:
            request = Request(record.file_url, headers={"User-Agent": USER_AGENT})
            with urlopen(request, timeout=180) as response, record.local_path.open("wb") as handle:
                while True:
                    chunk = response.read(1024 * 1024)
                    if not chunk:
                        break
                    handle.write(chunk)
        except Exception as exc:  # noqa: BLE001
            status = "failed"
            error = f"{type(exc).__name__}: {exc}"
            if record.local_path.exists() and record.local_path.stat().st_size == 0:
                record.local_path.unlink()

    size = record.local_path.stat().st_size if record.local_path.exists() else 0
    checksum = sha256_file(record.local_path) if size else ""
    return {
        "brand": record.brand,
        "source_name": record.source_name,
        "source_url": record.source_url,
        "link_text": record.link_text,
        "file_url": record.file_url,
        "local_path": str(record.local_path),
        "file_ext": record.ext,
        "status": status,
        "bytes": str(size),
        "sha256": checksum,
        "downloaded_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "elapsed_seconds": f"{time.time() - start:.2f}",
        "note": record.note,
        "error": error,
    }


def write_csv(path: Path, rows: Iterable[dict[str, str]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def write_index(manifest_rows: list[dict[str, str]]) -> None:
    index_path = CATALOG_ROOT / "equipment_drawings_index.md"
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    downloaded = [row for row in manifest_rows if row["status"] in {"downloaded", "exists"}]
    failed = [row for row in manifest_rows if row["status"] == "failed"]
    brands = sorted({row["brand"] for row in downloaded})

    lines = [
        "# 厂家设备图纸/BIM知识库索引",
        "",
        f"更新时间：{now}",
        "",
        "## 已下载范围",
        "",
        f"- 已下载或已存在文件数：{len(downloaded)}",
        f"- 下载失败文件数：{len(failed)}",
        f"- 覆盖品牌：{', '.join(brands) if brands else '无'}",
        "- 文件根目录：`F:\\产品知识库\\厂家设备图纸\\official_bim_cad`",
        "- 明细清单：`F:\\产品知识库\\厂家设备图纸\\catalog\\download_manifest.csv`",
        "",
        "## 已下载来源",
        "",
    ]
    for source in SOURCE_PAGES:
        count = sum(1 for row in downloaded if row["source_url"] == source.url)
        lines.append(f"- {source.brand}｜{source.source_name}：{count} 个文件")
        lines.append(f"  - 来源：{source.url}")
    lines.extend(["", "## 需要人工或登录补齐的来源", ""])
    for item in BLOCKED_SOURCES:
        lines.append(f"- {item['brand']}｜{item['source_name']}：{item['status']}")
        lines.append(f"  - 来源：{item['url']}")
        lines.append(f"  - 原因：{item['reason']}")
    lines.extend(
        [
            "",
            "## 使用规则",
            "",
            "- 后续设计制图优先使用本目录中有厂家来源和校验值的文件。",
            "- 登录、短信、下载额度、购物车流程的厂家库不自动抓取；需要人工登录后再导入，并补充来源页、下载时间和文件校验。",
            "- 第三方图库未纳入本批下载，避免图纸来源和版权边界不清。",
        ]
    )
    index_path.write_text("\n".join(lines) + "\n", encoding="utf-8-sig")


def main() -> int:
    os.makedirs(FILES_ROOT, exist_ok=True)
    os.makedirs(CATALOG_ROOT, exist_ok=True)

    records: list[LinkRecord] = []
    for source in SOURCE_PAGES:
        print(f"Discovering: {source.source_name}", flush=True)
        try:
            found = discover_links(source)
        except Exception as exc:  # noqa: BLE001
            print(f"  failed to discover {source.url}: {exc}", file=sys.stderr, flush=True)
            continue
        print(f"  found {len(found)} drawing links", flush=True)
        records.extend(found)

    rows: list[dict[str, str]] = []
    for index, record in enumerate(records, start=1):
        print(f"[{index}/{len(records)}] {record.brand} {record.local_path.name}", flush=True)
        rows.append(download(record))

    manifest_fields = [
        "brand",
        "source_name",
        "source_url",
        "link_text",
        "file_url",
        "local_path",
        "file_ext",
        "status",
        "bytes",
        "sha256",
        "downloaded_at_utc",
        "elapsed_seconds",
        "note",
        "error",
    ]
    write_csv(CATALOG_ROOT / "download_manifest.csv", rows, manifest_fields)
    write_csv(
        CATALOG_ROOT / "manual_download_sources.csv",
        BLOCKED_SOURCES,
        ["brand", "source_name", "url", "status", "reason", "note"],
    )
    write_index(rows)
    print(f"Wrote manifest: {CATALOG_ROOT / 'download_manifest.csv'}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
