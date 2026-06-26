from __future__ import annotations

import csv
from pathlib import Path

import ezdxf
from ezdxf.enums import TextEntityAlignment


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "outputs" / "6-12_plan_scan"
SRC_DXF = OUT_DIR / "6_12_plan_R2018.dxf"
OUT_DXF = OUT_DIR / "6_12_plan_room_boundary_draft.dxf"


DEFAULT_SIZES = {
    "会议/洽谈": (6500, 4500),
    "接待/休闲": (7000, 5000),
    "办公": (5200, 3800),
    "辅助用房": (3600, 2800),
    "包厢/会客": (5000, 3800),
    "辅助/清洗": (3200, 2600),
    "有办公家具未命名": (2800, 2200),
}


def load_rows() -> list[dict[str, str]]:
    with (OUT_DIR / "room_load_draft.csv").open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def rect_points(cx: float, cy: float, width: float, height: float) -> list[tuple[float, float]]:
    half_w = width / 2
    half_h = height / 2
    return [
        (cx - half_w, cy - half_h),
        (cx + half_w, cy - half_h),
        (cx + half_w, cy + half_h),
        (cx - half_w, cy + half_h),
    ]


def add_layer_if_missing(doc: ezdxf.EzDxfDocument, name: str, color: int) -> None:
    if name not in doc.layers:
        doc.layers.add(name, color=color)


def main() -> None:
    doc = ezdxf.readfile(SRC_DXF)
    msp = doc.modelspace()

    add_layer_if_missing(doc, "ROOM_BOUNDARY_DRAFT", 1)
    add_layer_if_missing(doc, "ROOM_ID_DRAFT", 3)
    add_layer_if_missing(doc, "ROOM_BOUNDARY_NOTE", 2)

    output_rows: list[dict[str, object]] = []
    for row in load_rows():
        name = row["房间名称"].strip()
        function = row["房间功能建议"].strip()
        try:
            cx = float(row["文字坐标X"])
            cy = float(row["文字坐标Y"])
        except ValueError:
            continue

        width, height = DEFAULT_SIZES.get(function, (4500, 3200))
        if name.startswith("R-6-12-WM"):
            width, height = DEFAULT_SIZES["有办公家具未命名"]

        points = rect_points(cx, cy, width, height)
        polyline = msp.add_lwpolyline(points, close=True, dxfattribs={"layer": "ROOM_BOUNDARY_DRAFT"})
        polyline.dxf.color = 1
        polyline.dxf.lineweight = 35

        msp.add_text(
            name,
            dxfattribs={"layer": "ROOM_ID_DRAFT", "height": 300, "color": 3},
        ).set_placement((cx, cy + height / 2 + 450), align=TextEntityAlignment.MIDDLE_CENTER)
        msp.add_text(
            "DRAFT-待复核",
            dxfattribs={"layer": "ROOM_BOUNDARY_NOTE", "height": 220, "color": 2},
        ).set_placement((cx, cy - height / 2 - 350), align=TextEntityAlignment.MIDDLE_CENTER)

        area_m2 = width * height / 1_000_000
        output_rows.append(
            {
                "房间名称": name,
                "房间功能建议": function,
                "中心X": round(cx, 3),
                "中心Y": round(cy, 3),
                "草稿宽度mm": width,
                "草稿高度mm": height,
                "草稿面积m2": round(area_m2, 2),
                "边界图层": "ROOM_BOUNDARY_DRAFT",
                "状态": "草稿矩形边界，需按真实墙体/隔断人工复核",
            }
        )

    doc.saveas(OUT_DXF)

    csv_path = OUT_DIR / "room_boundary_draft_index.csv"
    with csv_path.open("w", encoding="utf-8-sig", newline="") as f:
        fieldnames = list(output_rows[0].keys()) if output_rows else []
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(output_rows)

    print(f"rooms={len(output_rows)}")
    print(f"dxf={OUT_DXF}")
    print(f"index={csv_path}")


if __name__ == "__main__":
    main()
