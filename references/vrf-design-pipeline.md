# VRF 设计报价自动化管线

## 目标

`scripts/vrf_design_pipeline.py` 用于把明确指定的 CAD 输入整理成可复核底稿：

- 登记输入资料、修改时间和 SHA256。
- 读取 DXF 文字、闭合多段线和房间候选。
- 用闭合房间边界或附近面积文字生成房间面积。
- 按房间功能建议单位冷负荷，计算房间冷负荷。
- 生成室内机形式、容量和型号候选。
- 输出 Excel、CSV、Markdown 报告和室内机布置草图 DXF。

脚本不直接修改原始图纸；所有成果写入 `outputs/<task-name>/`。

## 输入要求

首选输入：

- `.dxf`：可直接读取。
- `.dwg`：需先通过 ODA File Converter 转为 DXF 后读取。

待转换输入：

- `.dwf`、`.dwfx`、`.pdf`：脚本先登记并列为待确认；后续需走 DWG/DXF 转换或 OCR 路线。

脚本不会默认扫描桌面或项目根目录。必须用 `--input` 明确指定文件路径。

## 基本命令

```powershell
python .\scripts\vrf_design_pipeline.py `
  --input "outputs\6-12_plan_scan\6_12_plan_R2018.dxf" `
  --task-name vrf_design_pipeline_demo `
  --city 杭州 `
  --brand 格力 `
  --series GMV
```

## 关键参数

| 参数 | 说明 |
| --- | --- |
| `--input` | 输入图纸路径，可重复传入多个文件 |
| `--task-name` | 输出目录名，位于 `outputs/` 下 |
| `--city` | 项目城市，用于后续气象参数和负荷口径追溯 |
| `--brand` | 候选品牌 |
| `--series` | 候选系列 |
| `--unit-scale` | CAD 单位换算到米，默认 `0.001`，即图纸单位为 mm |
| `--correction-factor` | 冷负荷统一修正系数，默认 `1.0` |
| `--min-room-area-m2` | 闭合多段线识别为房间的最小面积 |
| `--max-room-area-m2` | 闭合多段线识别为房间的最大面积 |

## 输出文件

| 文件 | 用途 |
| --- | --- |
| `source_register.csv` | 输入资料登记 |
| `text_entities.csv` | 图纸文字图元抽取 |
| `room_load_draft.csv` | 房间面积和冷负荷底稿 |
| `indoor_unit_selection_draft.csv` | 室内机选型候选 |
| `issue_ledger.csv` | 待确认事项和风险 |
| `vrf_design_quote_draft.xlsx` | 汇总工作簿 |
| `vrf_design_quote_report.md` | 设计报价底稿报告 |
| `vrf_indoor_unit_overlay_draft.dxf` | 室内机候选布置草图，可叠到 CAD 中复核 |

## 当前边界

- 自动识别只把闭合多段线或面积文字作为面积来源。
- 不把家具、天花造型、装饰线自动当成房间边界定稿。
- 单位冷负荷是经验建议，最终需设计师结合城市气象、围护结构、朝向、新风和人员密度确认。
- 型号候选是容量占位命名，正式型号必须回查厂家样册、设计选型手册或安装维修手册。
- 系统划分、室外机配比、管径、管长、分歧管和冷媒追加是下一阶段。
