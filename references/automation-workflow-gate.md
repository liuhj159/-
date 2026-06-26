# 自动化工作流入口门禁

## 目的

本门禁用于防止把桌面、项目目录或客户图纸当作试验材料自动处理。正式项目资料必须由用户明确指定输入路径和交付目标；非项目验证只能使用 `tests/fixtures/` 下的夹具文件。

## 运行模式

| 模式 | 用途 | 允许输入 | 禁止事项 |
| --- | --- | --- | --- |
| `formal_project` | 用户指定的正式项目资料登记、抽取和交付 | 用户明确给出的文件或目录 | 不得默认扫描桌面、项目根目录或外部图纸 |
| `non_project_fixture` | 验证脚本结构、输出模板和字段链路 | `tests/fixtures/` 下的非项目样例 | 不得读取任何真实项目图纸、截图或客户表格 |

## 标准命令

```powershell
python .\scripts\vrf_workflow_pilot.py --purpose non_project_fixture --input tests\fixtures\workflow_sample --clean-output
```

正式项目运行时必须把 `--purpose` 改为 `formal_project`，并显式传入用户指定的资料路径。

## 交付物

- `source_register.csv`：资料登记和 SHA256。
- `automation_assessment.csv`：自动化可读性和下一步工具需求。
- `issue_ledger.csv`：缺口和风险台账。
- `workflow_pilot.xlsx`：上述三张表的 Excel 汇总。
- `workflow_pilot_report.md`：可读报告。

## 关键约束

- 原始资料只读。
- 输出仅写入 `outputs/` 下任务目录。
- 每条关键结论必须有来源文件、版本、哈希、单元格、图纸标注或人工假设。
- 飞书库存未接 API 前，只使用用户导出的 Excel/CSV 快照，并记录导出时间。
- 飞书和千问接入状态必须在任务开始时检查；只记录凭据是否已配置，不输出密钥明文。
- 未明确开启 `ALLOW_EXTERNAL_UPLOAD=true` 前，不得自动上传客户图纸、报价文件或项目资料到外部系统。
- 未明确开启 `ALLOW_LLM_DOCUMENT_ANALYSIS=true` 前，不得把客户原始图纸、报价表或敏感资料发送给外部大模型。
- 厂家资料优先使用官方或专业可靠来源；登录、额度、购物车、短信验证等流程只记录为待人工补齐，不绕过。
