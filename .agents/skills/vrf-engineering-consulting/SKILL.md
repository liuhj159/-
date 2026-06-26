---
name: vrf-engineering-consulting
description: Organize VRF / multi-split HVAC engineering consulting work across design checking, quantity takeoff, BOM and inventory matching, cost estimating, quote preparation, audit review, and automation planning. Use when working with HVAC project files such as DWG, DWFX, DXF, PDF, screenshots, Excel施工任务单, BOM, inventory exports, price tables, quantity-check workbooks, engineering SOPs, or when the user asks for a multi-agent engineering design consulting team.
---

# VRF Engineering Consulting

## Overview

Run a structured multi-agent workflow for VRF / multi-split HVAC engineering consulting. Keep the main thread focused on scope, decisions, deliverables, and risk while role agents handle design, quantity, cost, audit, and automation work.

## Start

1. Register source materials first: file path, type, version/date, owner role, intended use, and missing information.
2. Read project SOPs when present: `多Agent工作团队SOP.md`, `多Agent岗位SOP细则.md`, and `多Agent角色提示词模板.md`.
3. If the user asks for parallel role work, spawn custom agents where available: `designer`, `cost-estimator`, `auditor`, and `automation-engineer`; keep `commander` logic in the main thread unless the user asks otherwise.
4. Keep original source files read-only. Write derived outputs under `outputs/<task-name>/`.
5. Attach source evidence to every key conclusion: drawing mark, sheet name, cell address, formula, screenshot, file version, or explicit assumption.
6. Treat the user's Feishu inventory table as the inventory source of truth. Prefer warehouse spot stock for design-compatible selection and quotation.
7. For manufacturer design standards, use `references/brand-design-rules.md` for quick structured lookup, then verify against `references/brand-standards-index.md` and cite the original `F:\产品知识库` path plus page/section.
8. For equipment drawings, BIM families, CAD blocks, or device dimensions, use `references/equipment-drawings-index.md` and cite the original local file path plus source URL/checksum from the manifest.

## Workflow

### 1. Command Intake

- Confirm scope: design check, quantity check, cost/quote, audit, automation, or full project handoff.
- Build a material register with source IDs such as `SRC-001`.
- List missing standards, manufacturer manuals, inventory exports, unit prices, tax/profit rules, and version conflicts.

### 2. Design Workstream

- Check equipment selection, system grouping, indoor/outdoor matching, connected capacity ratio, pipe length, height difference, branch pipe model, and refrigerant addition rules.
- Produce a design check table and design issue list.
- Do not decide price, procurement substitution, or final commercial strategy.

### 3. Quantity And Cost Workstream

- Extract or reconcile quantities for copper pipe, insulation, refrigerant, condensate pipe, wiring, supports, branch pipes, accessories, and labor.
- Compare drawing quantity, BOM quantity, table quantity, confirmed quantity, unit, conversion rule, and difference.
- Match Feishu inventory and price data when provided; record Feishu table/export source, export time, stock status, available quantity, substitute model, unit price source, loss rate, labor, tax, management fee, and profit assumptions.
- Quote priority is `spot stock available` first, then `design-approved substitute`, then `purchase required`, then `pending confirmation`.
- Produce quantity, cost, quote-base, and variance-tracking tables.

### 4. Audit Workstream

- Review versions, formulas, units, mappings, quantity deltas, commercial assumptions, logs, and closure evidence.
- Check whether quotation items correctly prioritize Feishu warehouse spot stock and whether substitutions have design approval.
- Grade issues as `S1` block, `S2` must fix and recheck, `S3` limited-risk fix, or `S4` formatting/wording cleanup.
- Produce an audit issue ledger and release conclusion.

### 5. Automation Workstream

- Identify repeatable extraction and reconciliation steps for CAD/DWG, DXF, PDF/OCR, Excel, inventory tables, and RPA.
- Prefer read-only extraction first, then semi-automatic confirmation, then controlled write-back.
- Produce a data dictionary, automation priority list, script proposal, and manual review checkpoints.

## Output Contract

For full project work, return:

- Source material register.
- Design check summary.
- Quantity and cost reconciliation summary.
- Audit issue ledger with severity and owner.
- Automation opportunities and manual review points.
- Paths to generated workbooks, reports, images, scripts, or logs.
- Clear pending questions for the user.

## References

- Read `references/tables-and-ledgers.md` when creating or reviewing deliverable table schemas.
- Read `../../../references/brand-design-rules.md` for a quick structured table of common brand design rules.
- Read `../../../references/brand-standards-index.md` when selecting brand manuals, design standards, pipe rules, indoor/outdoor matching limits, or price-table sources.
- Read `../../../references/equipment-drawings-index.md` when using manufacturer BIM/CAD/drawing files, Revit families, IFC files, or equipment model dimensions.
- Read existing project SOP files before changing role boundaries or workflow order.
