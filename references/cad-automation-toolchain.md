# CAD/DWG 自动化工具链状态

## 当前状态

| 工具 | 用途 | 本机状态 | 说明 |
| --- | --- | --- | --- |
| Python | 脚本执行、表格和报告生成 | 已安装 | 当前脚本已通过 `py_compile` 和实际运行验证 |
| openpyxl | Excel 工作簿读取和成果表生成 | 已安装 | 已生成 `workflow_pilot.xlsx` 和 Excel 工作簿索引 |
| Pillow | 图片尺寸和预览资源识别 | 已安装 | 用于 DWFX/图片类派生资源识别 |
| ezdxf | DXF 图元、文字、块属性读取 | 已安装 | 等待 DXF 输入或 DWG 转换链路 |
| ODA File Converter | DWG 转 DXF | 已安装到项目 `tools/ODAFileConverter/` | 使用 ODA 官方 Windows x64 MSI 当前用户安装；未加入系统 PATH，脚本需显式配置路径 |

## 官方来源

- ODA File Converter 官方页：`https://www.opendesign.com/guestfiles/oda_file_converter`
- ezdxf ODA File Converter 支持说明：`https://ezdxf.readthedocs.io/en/stable/addons/odafc.html`

ODA 官方说明其 File Converter 支持 DWG/DXF 版本转换，并提供图形界面和命令行接口；ezdxf 官方文档说明可调用已安装的 ODA File Converter 将 DWG/DXB/DXF 转为临时 DXF 后读取。

## 安装后的验证命令

```powershell
python - <<'PY'
from ezdxf.addons import odafc
print(odafc.is_installed())
PY
```

PowerShell 中可用兼容写法：

```powershell
@'
from ezdxf.addons import odafc
print(odafc.is_installed())
'@ | python -
```

返回 `True` 后，再对用户明确授权的正式项目 DWG 运行 DWG -> DXF -> ezdxf 图元抽取验证。

## 本次安装记录

- 官方下载页：`https://www.opendesign.com/guestfiles/TeighaFileConverter`
- 下载文件：`tools/ODAFileConverter_QT6_vc16_amd64dll_27.1.msi`
- SHA256：`3D5961F510CF95F398B8E2920899DC8E8C51ADECDAF5B20A40B3D1A29269DE81`
- 签名状态：Windows `Get-AuthenticodeSignature` 验证为 `Valid`
- 全用户静默安装失败：错误 `1925`，需要管理员权限写入 `C:\Program Files`
- 当前用户安装成功：`tools/ODAFileConverter/ODAFileConverter.exe`
- ezdxf 配置方式：在运行进程中设置 `ezdxf.options.set('odafc-addon', 'win_exec_path', '<项目路径>/tools/ODAFileConverter/ODAFileConverter.exe')`

## 西投云城项目第一步状态

- 输入目录：`C:\Users\Liugq\Desktop\施工图-西投云城犀谷7#楼7-8层装修工程(1)`
- 已登记：14 个 DWG、2 个 Excel。
- 已排除：`.dwl`、`.dwl2` 等 CAD 临时锁文件。
- 已生成：`outputs/xitou_yuncheng_intake/`
- 当前状态：ODA File Converter 已可用，已对 7F 装饰平顶面图副本完成 DWG -> DXF 转换验证。
- 验证输出：`outputs/dwg_conversion_test/`
- 注意：7F 装饰平顶面图不是暖通主图，但转换后文字中已可识别 `新风`、`冷媒`、`送风` 等暖通相关交叉条件，可作为后续设计条件抽取入口。
