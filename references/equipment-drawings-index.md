# 厂家设备图纸/BIM索引

本索引连接外部产品知识库中的厂家设备图纸、BIM族和CAD相关文件。不要复制整库到项目目录；设计制图时直接引用知识库路径，并在成果中记录来源页、下载时间和文件校验。

## 知识库位置

- 文件根目录：`F:\产品知识库\厂家设备图纸\official_bim_cad`
- 清单目录：`F:\产品知识库\厂家设备图纸\catalog`
- 下载明细：`F:\产品知识库\厂家设备图纸\catalog\download_manifest.csv`
- 人工补齐来源：`F:\产品知识库\厂家设备图纸\catalog\manual_download_sources.csv`
- F盘索引：`F:\产品知识库\厂家设备图纸\catalog\equipment_drawings_index.md`

## 当前已下载范围

首批只纳入厂家官方或厂家官方页面公开暴露的直接下载文件，不纳入第三方图库。

| 品牌 | 来源 | 文件数 | 本地目录 |
| --- | --- | ---: | --- |
| Haier | Haier HVAC Europe BIM Downloads | 54 | `F:\产品知识库\厂家设备图纸\official_bim_cad\Haier_HVAC_EU_BIM` |
| Carrier | Carrier Ductless Systems Revit Templates | 18 | `F:\产品知识库\厂家设备图纸\official_bim_cad\Carrier_US_Revit_Ductless` |
| Carrier / Toshiba Carrier | Carrier and Toshiba Carrier VRF Revit Templates | 28 | `F:\产品知识库\厂家设备图纸\official_bim_cad\Carrier_US_Revit_VRF` |
| Trane | Trane Thermal Energy Storage BIM | 23 | `F:\产品知识库\厂家设备图纸\official_bim_cad\Trane_US_Thermal_Energy_Storage_Revit` |

合计：123 个文件，约 75.23 MB；其中 71 个 ZIP、29 个 IFC、23 个 RFA。

## 待人工或登录补齐来源

| 品牌 | 来源 | 状态 | 原因 |
| --- | --- | --- | --- |
| 大金 | Daikin China BIM Download | manual_or_dynamic | 官方页面可访问，但静态页面没有直接文件地址 |
| 大金 | Daikin Global BIM Library | cart_or_login_flow | 可浏览机型和 Revit 版本，下载走购物车/登录流程 |
| 美的 | Midea Goujianwu Revit Library | login_quota_required | 构件坞页面有 RFA、尺寸和立即下载，但要求登录/短信/额度 |
| 格力 | Gree Goujianwu Revit Library | login_quota_required | 构件坞页面有 RFA 和下载控件，但下载受登录/额度限制 |
| 三菱电机 | Mitsubishi Electric Trane MPro Product Pages | javascript_api_needs_followup | 渲染页面可见 CAD/Revit 文档，静态抓取只返回前端壳 |
| 三星 | Samsung HVAC Technical Documents | dynamic_search_needs_followup | 官方文档搜索可见 REVIT BIM/DWG 类结果，但静态抓取没有直接文件地址 |
| LG | LG HVAC BIM Library | partner_platform | 官方 LG 页面指向 BIMsmith 合作库，静态页面没有直接文件地址 |
| Panasonic | Panasonic North America BIM Library | partner_platform | 官方页面说明可下载 BIM/Revit，但静态页面没有直接文件地址 |
| 三菱重工 | MHI Building Information Modelling | partner_search_service | 官方页面说明 VRF/RAC/PAC Revit BIM 支持，并使用 MEPcontent 搜索服务 |
| Trane | Trane Generated BIM-Revit Request Flow | email_request_flow | Trane 同页部分设备 Revit 文件需要填写邮箱后生成发送；本次只自动下载直接 RFA |

## 使用规则

1. 制图、族引用、设备外形尺寸核对时，先查 `download_manifest.csv`，再打开对应本地文件。
2. 每次引用必须记录：品牌、型号或系列、本地路径、来源 URL、下载时间、SHA256。
3. ZIP 内的 RFA/RVT/IFC/DWG/DXF 解压后如果进入项目成果目录，应保留原 ZIP 路径和清单行，不覆盖原始下载文件。
4. 登录、短信、额度、购物车流程的厂家库需要人工登录下载后再导入，并补录到清单；不得用非授权方式绕过。
5. 第三方图库只有在用户明确允许时才纳入，并必须标记为“非厂家官方来源”。

## 更新脚本

- 脚本：`scripts/download_public_bim_cad.py`
- 运行目录：`C:\Users\Liugq\Desktop\工程设计咨询团队`
- 命令：`python .\scripts\download_public_bim_cad.py`

脚本可重复运行；已有文件会标记为 `exists`，不会重复下载。
