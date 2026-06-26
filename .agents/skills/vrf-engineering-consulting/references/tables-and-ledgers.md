# Tables And Ledgers

Use these table schemas as defaults. Add columns only when the source evidence or project scope requires them.

## Source Register

| Field | Purpose |
| --- | --- |
| source_id | Stable ID such as `SRC-001` |
| file_or_link | Local file path or external link |
| type | drawing, bim_family, ifc_model, cad_block, standard, equipment table, BOM, inventory, price table, screenshot, log |
| version_date | Version, receive date, or export date |
| owner_role | designer, cost-estimator, auditor, automation-engineer, commander |
| status | used, pending confirmation, obsolete |
| notes | Scope, caveat, or missing information |

## Design Check

| Field | Purpose |
| --- | --- |
| system_id | System number |
| segment_id | Pipe or branch segment |
| start_point | Outdoor unit, branch pipe, indoor unit, or drawing mark |
| end_point | Downstream target |
| downstream_units | Indoor unit IDs downstream |
| downstream_capacity | kW, HP, or project-defined unit |
| expected_liquid_pipe | Standard liquid pipe spec |
| expected_gas_pipe | Standard gas pipe spec |
| drawing_liquid_pipe | Drawing marked liquid pipe spec |
| drawing_gas_pipe | Drawing marked gas pipe spec |
| conclusion | pass, undersized, oversized, pending |
| evidence | Manual row, drawing mark, sheet, or assumption |

## Quantity Check

| Field | Purpose |
| --- | --- |
| item | copper pipe, insulation, refrigerant, condensate, wiring, branch pipe, support, labor |
| spec | Diameter, model, or material spec |
| drawing_qty | Quantity from drawing or drawing takeoff |
| table_qty | Quantity from施工任务单, BOM, or quote table |
| confirmed_qty | Quantity used for cost/quote |
| unit | m, pcs, kg, set, item |
| conversion_rule | Unit conversion or loss factor |
| difference | table_qty minus drawing_qty, or project-defined delta |
| conclusion | match, table higher, table lower, pending |
| evidence | Sheet/cell, drawing mark, formula, screenshot |
| owner | designer or cost-estimator |

## Cost And Quote

| Field | Purpose |
| --- | --- |
| category | Material or labor category |
| spec_model | Matched spec/model |
| confirmed_qty | Quantity used for pricing |
| feishu_inventory_source | Feishu table name, export file, or API source |
| inventory_snapshot_time | Export or API read time |
| material_code | Inventory material code |
| stock_available | Inventory quantity or status |
| spot_stock_qty | Warehouse spot stock quantity available for quotation |
| inventory_status | spot stock available, insufficient, purchase required, substitute pending, unmatched |
| substitute_model | Candidate substitute model when original design model is unavailable |
| design_approval | approved, rejected, pending, not required |
| purchase_suggestion | stock first, purchase, substitute, pending |
| unit_price | Price before or after tax as defined |
| price_source | Inventory, supplier quote, history, estimate |
| material_cost | confirmed_qty * unit_price |
| labor_cost | Rule-based labor amount |
| management_fee | Rate or amount |
| profit | Rate or amount |
| tax | Tax rate or amount |
| quote_total | Final quote amount |
| assumptions | Commercial assumptions and exclusions |

## Issue Ledger

| Field | Purpose |
| --- | --- |
| issue_id | `QA-001` style ID |
| severity | S1, S2, S3, S4 |
| source | design, quantity, cost, quote, automation, version |
| description | Concise issue statement |
| impact | System, segment, material, amount, or delivery impact |
| evidence | File, sheet/cell, drawing mark, formula, screenshot, log |
| owner | Responsible role |
| recommendation | Corrective action |
| status | open, in progress, fixed, rechecked, accepted risk |
| release_conclusion | pass, conditional pass, fail |
