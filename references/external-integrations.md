# 外部系统与密钥接入说明

## 目标

工作资料整理层应预留飞书和千问接入能力：

- 飞书：库存主数据、报价模板、项目资料夹、图纸方案上传、审批/协作记录。
- 千问：图纸文字理解、资料分类、长文档摘要、问题台账归纳等辅助分析。

## 密钥管理

- 真实密钥只允许放在本机 `.env`、系统环境变量或受控密钥管理器中。
- 不得把密钥写入 `AGENTS.md`、脚本、报告、Excel、CSV、Markdown 输出或 Git 提交。
- `.env.example` 只保留变量名和用途说明，不包含真实值。
- 任何脚本打印配置时必须自动屏蔽密钥，只显示是否已配置。

## 飞书接入字段

- `FEISHU_APP_ID`
- `FEISHU_APP_SECRET`
- `FEISHU_TENANT_ACCESS_TOKEN`
- `FEISHU_APP_TOKEN`
- `FEISHU_INVENTORY_TABLE_ID`
- `FEISHU_INVENTORY_VIEW_ID`
- `FEISHU_WRITABLE_APP_TOKEN`
- `FEISHU_WRITABLE_TABLE_ID`
- `FEISHU_WRITABLE_TABLE_NAME`
- `FEISHU_QUOTE_TEMPLATE_FILE_TOKEN`
- `FEISHU_PROJECT_FOLDER_TOKEN`

用途：

- 读取飞书库存表和价格表。
- 创建或复制报价模板。
- 上传项目图纸方案、设备表、工程量表、报价底稿和问题台账。
- 回写库存匹配、报价状态和待确认事项。

## 千问接入字段

- `DASHSCOPE_API_KEY`
- `QWEN_MODEL`

用途：

- 对图纸导出的文字、PDF 文本、厂家资料和问题台账做辅助分类与摘要。
- 不替代设计结论；所有输出必须保留来源和人工复核状态。

## 上传边界

- `ALLOW_EXTERNAL_UPLOAD=false` 时，不得自动上传图纸、客户资料或报价文件到外部系统。
- `ALLOW_LLM_DOCUMENT_ANALYSIS=false` 时，不得把客户原始图纸、报价表或敏感资料发送给外部大模型。
- 开启上传或模型分析前，必须确认目标系统、资料范围和输出路径。

## 当前落地顺序

1. 先接飞书项目资料夹和报价模板，打通图纸方案上传与模板复制。
2. 再接飞书库存表，做库存优先匹配和报价基础表回写。
3. 最后接千问辅助资料整理，只处理可追溯的提取文本和派生底稿，保留人工复核。

## 报价模板上传流程

生成飞书导入包：

```powershell
python .\scripts\prepare_feishu_quote_template_import.py
```

检查飞书/千问配置状态：

```powershell
python .\scripts\check_external_integrations.py
```

只读同步飞书多维表格库存/价格表快照：

```powershell
python .\scripts\sync_feishu_bitable.py --url "https://ncnr5lir59ia.feishu.cn/base/HJRKbwEsiaIXlCstXxjcBW5dnNY?table=tblBej3wwa6dk5ed&view=vewQipduTI"
```

同步结果输出到 `outputs/feishu_inventory_sync/`，包括：

- `feishu_inventory_snapshot.csv`：用于库存优先匹配和报价基础表的本地只读快照。
- `feishu_inventory_records.json`：保留飞书字段原始结构，便于追溯。
- `sync_manifest.json`：记录同步时间、表格 token、视图 ID、记录数和 SHA256。

从 CSV 上传或回写到飞书多维表格：

```powershell
# 追加新记录，默认 dry-run，不会真实写入
python .\scripts\write_feishu_bitable.py --mode create --csv .\outputs\feishu_inventory_sync\feishu_inventory_snapshot.csv --url "https://ncnr5lir59ia.feishu.cn/base/HJRKbwEsiaIXlCstXxjcBW5dnNY?table=tblBej3wwa6dk5ed&view=vewQipduTI"

# 按 _record_id 回写已有记录，默认 dry-run，不会真实写入
python .\scripts\write_feishu_bitable.py --mode update --csv .\outputs\feishu_inventory_sync\feishu_inventory_snapshot.csv --url "https://ncnr5lir59ia.feishu.cn/base/HJRKbwEsiaIXlCstXxjcBW5dnNY?table=tblBej3wwa6dk5ed&view=vewQipduTI"
```

真实写入必须同时满足：

- `.env` 已配置 `FEISHU_APP_ID`、`FEISHU_APP_SECRET`，或配置有效 `FEISHU_TENANT_ACCESS_TOKEN`。
- `.env` 中 `ALLOW_EXTERNAL_UPLOAD=true`。
- 命令显式增加 `--execute`。
- 飞书应用已获得目标多维表格的读写权限。
- 写入目标必须匹配 `.env` 中的 `FEISHU_WRITABLE_APP_TOKEN` 和 `FEISHU_WRITABLE_TABLE_ID`；当前唯一允许写入表为 `工程设计报价`。

飞书上传脚本默认只做 dry-run，不会上传：

```powershell
python .\scripts\upload_feishu_quote_template.py
```

确认 `.env` 已配置、`ALLOW_EXTERNAL_UPLOAD=true`，并明确要上传后，才执行：

```powershell
python .\scripts\upload_feishu_quote_template.py --execute
```

当前脚本先把 Excel 模板上传到飞书项目资料夹；如需转换为飞书在线电子表格，应在飞书 Drive 上传成功后继续接入飞书导入任务接口。
