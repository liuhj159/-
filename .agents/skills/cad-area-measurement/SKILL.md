---
name: cad-area-measurement
description: Extract and standardize room areas from AutoCAD AREA command demonstrations, screenshots, or recorded videos for HVAC/VRF design workflows. Use when the user shows CAD area measurement, asks to learn their CAD measuring method, asks to update room names/areas from video, or asks to fill room area, cooling load, and equipment selection drafts from manually measured CAD results.
---

# CAD Area Measurement

## Purpose

Use this skill to turn the user's AutoCAD measuring workflow into traceable room-area data for VRF/HVAC design and quotation drafts.

The preferred method is manual AutoCAD `AREA` point-pick measurement when drawings do not contain reliable closed room boundaries.

## Source Rules

- Keep original DWG/DXF/DWF/PDF/video files read-only.
- Treat clear AutoCAD `AREA` command output or user-added CAD text as stronger evidence than automatic wall-line estimates.
- Do not treat furniture, desks, cabinets, decorative lines, ceiling patterns, or hatch graphics as room boundaries.
- Close door openings back to the wall boundary for area measurement.
- Measure open or semi-open spaces by actual air-conditioning service area.
- If the area or room name is not readable, mark it as `pending_review_unreadable_video` instead of guessing.

## Video/Screenshot Review Workflow

1. Register the media file path, timestamp, and purpose.
2. Extract frames around relevant actions if a video is provided.
3. Identify each measurable event:
   - room name shown on drawing;
   - `AREA` command point-pick boundary;
   - command-line area and perimeter result;
   - user-added room name or area text.
4. Record evidence:
   - video file name;
   - timestamp or frame file;
   - screenshot path if available;
   - visible command-line result or visible CAD text.
5. Convert units:
   - if CAD is in mm, `area_m2 = area_cad / 1000000`;
   - if CAD is in mm, `perimeter_m = perimeter_cad / 1000`;
   - if user writes `30m2`, use `30.00` as already converted.
6. Update the room area table.
7. Recompute cooling load and indoor unit candidate selection.
8. Preserve uncertain values in the issue ledger.

## Evidence Priority

Use this order:

1. Clear AutoCAD command line: `area = ...`, `perimeter = ...`.
2. Clear user-added CAD text such as `room name 30m2`.
3. User explicit statement in chat.
4. Automatic DXF wall-coordinate estimate.
5. Furniture-cluster or screenshot estimate, only as pending candidate.

When a higher-priority source appears, overwrite lower-priority estimate values and keep the previous value in notes if useful.

## Required Output Fields

Use these fields for manual area records:

```csv
room_name,area_cad,perimeter_cad,area_m2,perimeter_m,cad_unit,method,evidence,status,notes
```

Recommended status values:

- `confirmed_by_user_area_command`
- `confirmed_by_user_cad_text`
- `estimated_from_cad_wall_axis`
- `pending_review_unreadable_video`
- `pending_room_name_confirmation`
- `not_a_room`

## Integration With VRF Drafts

After area updates:

- recompute `cooling_load_w = area_m2 * unit_load_w_m2 * correction_factor`;
- recompute `cooling_load_kw`;
- select the next standard indoor unit capacity above load;
- flag excessive or low capacity margins;
- keep brand/model as candidate until manufacturer manual verification.

For office rooms, use the project draft's current unit load unless the user gives a different design basis. Do not silently change load indicators.

## Current 6-12 Demonstration Facts

Known confirmed values from user screenshots/video:

| Room label | Area | Evidence |
| --- | ---: | --- |
| bidding department | 45.17 m2 | AutoCAD AREA command screenshot/video, CAD area 45168106.11 and perimeter 31970.00 |
| purchasing department | 30.00 m2 | User-added CAD text visible in video |
| reception/rest area | 118.31 m2 | User-added CAD text visible in video, pending full boundary review |

Keep the original Chinese room names in project CSV/XLSX outputs when the source file contains them.

If a clearer follow-up video contradicts these values, use the clearer source and note the replacement.

## Clear Recording Checklist

When asking the user for a better recording, ask them to show:

- full AutoCAD drawing area, not OBS recursive preview;
- room name before measurement;
- full `AREA` point-pick boundary;
- command line after pressing Enter, showing area and perimeter;
- any text they add to the drawing;
- one room per short clip when possible.

Prefer MKV or MP4. OBS display capture is safer than AutoCAD window capture.
