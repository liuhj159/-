from __future__ import annotations

import csv
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
KB_ROOT = Path(r"F:\产品知识库\产品样册及安装维修手册")
OUT_MD = PROJECT_ROOT / "references" / "brand-design-rules.md"
OUT_CSV = PROJECT_ROOT / "references" / "brand-design-rules.csv"


@dataclass(frozen=True)
class Source:
    brand: str
    series: str
    path: Path
    source_note: str


@dataclass(frozen=True)
class Category:
    name: str
    keywords: list[str]
    required_any: list[str]
    avoid: list[str]


SOURCES = [
    Source("格力", "GMV/通用", KB_ROOT / "格力" / "格力多联机选型设计手栅.pdf", "选型设计手册"),
    Source("格力", "GMVES", KB_ROOT / "格力" / "格力GMVES直流变频多联机技术服务手册.pdf", "技术服务手册"),
    Source("美的", "V8 大多联", KB_ROOT / "美的" / "V8-JZ-24-01A 大多联技术手册（2024.07）.pdf(1).pdf", "技术手册"),
    Source("美的", "多联王V/MDV7", KB_ROOT / "美的" / "美的多联王V安装使用手册.pdf", "安装使用手册"),
    Source("海尔", "RFC735MXSLYB", KB_ROOT / "海尔" / "RFC735MXSLYB(互联)安装使用说明书.pdf", "安装使用说明书"),
    Source("海尔", "顶出风多联", KB_ROOT / "海尔" / "海尔大单项目-顶出风多联机样册2025.pdf", "样册"),
    Source("日立", "FSG", KB_ROOT / "日立" / "【日立】FSG直流变频多联机技术手册（119页）(1) (2).pdf", "技术手册"),
    Source("日立", "SET-FREE V", KB_ROOT / "日立" / "日立SET-FREE V系列20231018.pdf", "样册"),
    Source("天加", "ARK II", KB_ROOT / "天加" / "A15923G03商用多联机ARK II系列样本 1107 Y.pdf", "样本"),
    Source("天加", "TIMS S", KB_ROOT / "天加" / "01说明书 TIMS 2-4代 S系列.pdf", "说明书"),
    Source("海信", "Hi Smart H+", KB_ROOT / "海信" / "多联机-海信Hi Smart H+系列20230830 (2).pdf", "样册"),
    Source("大金", "VRV X", KB_ROOT / "大金" / "VRVX维修手册.pdf", "维修手册"),
]


GLOBAL_AVOID = [
    "故障",
    "热敏",
    "通讯",
    "电阻",
    "开路",
    "短路",
    "电子膨胀阀",
    "压缩机",
    "检查模式",
    "冷冻机油",
    "油水分离器",
    "拆除",
    "过滤器",
    "传感器",
    "人感",
    "舒适",
]


CATEGORIES = [
    Category(
        "内外机配比",
        ["容量搭配", "搭配范围", "连接率", "容量比", "配比", "连接容量", "连接台数", "额定容量配比"],
        ["容量", "连接率", "配比", "搭配"],
        ["误配线", "电源", "检测", "db 亮"],
    ),
    Category(
        "配管长度与落差",
        ["配管长度", "管长", "总长", "高低差", "落差", "第一分歧", "等效长度"],
        ["配管", "管长", "落差", "高低差", "分歧"],
        ["通讯", "热敏", "故障", "电阻"],
    ),
    Category(
        "冷媒配管规格",
        ["冷媒配管", "制冷剂配管", "配管直径", "配管外径", "接管尺寸", "液管", "气管", "管径"],
        ["冷媒配管", "制冷剂配管", "配管直径", "配管外径", "接管尺寸", "管径", "液管(mm)", "气管(mm)", "Φ", "φ"],
        ["温度传感器", "排气管"],
    ),
    Category(
        "分歧管",
        ["分歧管", "分支管"],
        ["分歧管", "分支管"],
        ["故障", "通讯"],
    ),
    Category(
        "冷媒追加",
        ["追加制冷剂", "冷媒追加", "制冷剂追加", "追加冷媒"],
        ["追加", "冷媒", "制冷剂"],
        ["故障", "热敏", "通讯"],
    ),
    Category(
        "衰减与修正",
        ["配管长度、落差衰减", "能力修正", "长连管", "修正系数", "衰减"],
        ["能力", "配管长度", "落差", "管长", "长连管", "修正系数"],
        ["温度修正", "修正温度"],
    ),
]


def extract_pdf_pages(path: Path) -> list[str]:
    result = subprocess.run(
        ["pdftotext", "-layout", "-enc", "UTF-8", str(path), "-"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=120,
        check=False,
    )
    text = result.stdout.decode("utf-8", errors="replace")
    return text.split("\f") if text else []


def clean(text: str) -> str:
    text = re.sub(r"\s+", " ", text).strip()
    text = text.replace("|", "/")
    return text


def has_required_context(text: str, category: Category) -> bool:
    return any(token in text for token in category.required_any)


def avoid_penalty(text: str, category: Category) -> int:
    avoid_terms = GLOBAL_AVOID + category.avoid
    return sum(text.count(token) for token in avoid_terms) * 4


def page_score(page: str, category: Category, page_index: int) -> int:
    score = 0
    for keyword in category.keywords:
        score += page.count(keyword) * 3
    score -= avoid_penalty(page[:2000], category)
    if re.search(r"\d", page):
        score += 2
    if "mm" in page or "Φ" in page or "φ" in page:
        score += 2
    if "目录" in page[:500] or re.search(r"\.{5,}", page):
        score -= 6
    if page_index <= 3:
        score -= 2
    return score


def best_excerpt(page: str, category: Category) -> str:
    lines = [clean(line) for line in page.splitlines()]
    lines = [line for line in lines if line and not re.search(r"\.{8,}", line)]
    best_i = None
    best_score = -1
    for i, line in enumerate(lines):
        score = sum(line.count(keyword) for keyword in category.keywords) * 4
        context = " ".join(lines[max(0, i - 1) : min(len(lines), i + 3)])
        if not has_required_context(context, category):
            score -= 4
        score -= avoid_penalty(context, category)
        if re.search(r"\d", line):
            score += 2
        if "mm" in context or "Φ" in context or "φ" in context:
            score += 2
        if len(line) < 8:
            score -= 2
        if score > best_score:
            best_score = score
            best_i = i
    if best_i is None or best_score <= 0:
        return ""
    start = max(0, best_i - 1)
    end = min(len(lines), best_i + 3)
    excerpt = " / ".join(lines[start:end])
    return excerpt[:260]


def extract_rows() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for source in SOURCES:
        if not source.path.exists():
            rows.append(
                {
                    "brand": source.brand,
                    "series": source.series,
                    "source_note": source.source_note,
                    "rule_category": "文件状态",
                    "pdf_page": "",
                    "matched_keywords": "",
                    "evidence": "文件未找到",
                    "confidence": "low",
                    "source_path": str(source.path),
                }
            )
            continue

        try:
            pages = extract_pdf_pages(source.path)
        except Exception as exc:  # noqa: BLE001
            rows.append(
                {
                    "brand": source.brand,
                    "series": source.series,
                    "source_note": source.source_note,
                    "rule_category": "抽取状态",
                    "pdf_page": "",
                    "matched_keywords": "",
                    "evidence": f"抽取失败：{exc}",
                    "confidence": "low",
                    "source_path": str(source.path),
                }
            )
            continue

        for category in CATEGORIES:
            candidates = []
            for page_no, page in enumerate(pages, start=1):
                matched = [keyword for keyword in category.keywords if keyword in page]
                if not matched:
                    continue
                if not has_required_context(page, category):
                    continue
                score = page_score(page, category, page_no)
                excerpt = best_excerpt(page, category)
                if not excerpt:
                    continue
                candidates.append((score, page_no, matched, excerpt))
            if not candidates:
                continue
            candidates.sort(key=lambda item: (-item[0], item[1]))
            score, page_no, matched, excerpt = candidates[0]
            if score < 4:
                continue
            if avoid_penalty(excerpt, category) > 0:
                continue
            confidence = "high" if score >= 8 else "medium"
            rows.append(
                {
                    "brand": source.brand,
                    "series": source.series,
                    "source_note": source.source_note,
                    "rule_category": category.name,
                    "pdf_page": str(page_no),
                    "matched_keywords": "、".join(matched),
                    "evidence": excerpt,
                    "confidence": confidence,
                    "source_path": str(source.path),
                }
            )
    return rows


def write_csv(rows: list[dict[str, str]]) -> None:
    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "brand",
        "series",
        "rule_category",
        "pdf_page",
        "matched_keywords",
        "evidence",
        "confidence",
        "source_note",
        "source_path",
    ]
    with OUT_CSV.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_md(rows: list[dict[str, str]]) -> None:
    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# 常用品牌设计规则抽取表",
        "",
        "本表由 `scripts/extract_brand_design_rules.py` 从 `F:\\产品知识库\\产品样册及安装维修手册` 的厂家 PDF 中抽取。",
        "本表用于定位设计校核依据，不直接替代厂家手册原文；正式校核时必须回到源文件页码/章节复核。",
        "",
        "## 字段说明",
        "",
        "- `pdf_page` 是 PDF 提取页序号，用于快速定位；如厂家资料有印刷页码，以原文印刷页码为准。",
        "- `evidence` 是短片段，保留用于定位规则位置，不代表完整条文。",
        "- `confidence=high` 表示关键词和内容密集度较高；`medium` 仍需重点人工复核。",
        "",
    ]

    brands = sorted({row["brand"] for row in rows})
    for brand in brands:
        lines += [f"## {brand}", ""]
        lines.append("| 系列 | 规则类别 | PDF页 | 关键词 | 证据片段 | 置信度 | 来源 |")
        lines.append("| --- | --- | ---: | --- | --- | --- | --- |")
        for row in [r for r in rows if r["brand"] == brand]:
            source_label = f"{row['source_note']}：`{row['source_path']}`"
            values = [
                row["series"],
                row["rule_category"],
                row["pdf_page"],
                row["matched_keywords"],
                row["evidence"],
                row["confidence"],
                source_label,
            ]
            values = [value.replace("\n", " ").replace("|", "/") for value in values]
            lines.append("| " + " | ".join(values) + " |")
        lines.append("")
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    rows = extract_rows()
    rows.sort(key=lambda row: (row["brand"], row["series"], row["rule_category"], row["pdf_page"]))
    write_csv(rows)
    write_md(rows)
    print(f"Wrote {len(rows)} rows")
    print(OUT_MD)
    print(OUT_CSV)


if __name__ == "__main__":
    main()
