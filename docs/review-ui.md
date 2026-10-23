# Inspection review UI

Streamlit Application for reviewing the model's results on the 29 sample images. Results are drafts for human review; the app makes no accept or reject decisions.

## What it does
- **Overview:** summary metrics, class/mismatch/status filters, grid of overlays. Detected classes are colored chips using the same colors as the masks (`CLASS_COLORS` in `src/visualization.py`).
- **Detail:** original vs overlay with per-class toggles, dark blue navigation buttons (Back to grid, Previous, Next, Next unreviewed, styled by CSS in `NAV_CSS`), expected vs detected, findings, limitations, raw JSON.
- **Review:** verdict (agree, disagree, unsure) with a note and history. A note is required for disagree (max 2000 characters).
- **QC agent:** two clickable example questions plus a question box. Each question is answered independently (the agent has no memory of earlier turns). Turns are listed newest first, kept in the session only, and not saved. Handling guidance is available only through the agent, which reads `config/defect_guidance.json` via `qc_tools.lookup_defect_guidance`.

Flags: `extra_class`, `expected_missing`, `no_detection`. For example, `rolled-in_scale_4.jpg` also detects Pitted surface.

## Handling guidance
There is no guidance section in the page. Only entries with status `approved` are shown by default. The file is currently `draft_pending_review`, so by default the QC agent says guidance is unavailable for every class. To let the agent use the drafts for a demo, set the environment variable `QC_SHOW_DRAFT_GUIDANCE=1` on the Application and restart it. The agent then labels drafts as unreviewed and cites their sources. Patches has no guidance in either mode.

## Run
Create a Cloudera AI project from this repository as an AMP and enter `QC_LLM_BASE_URL`. The AMP downloads the 29 images, runs the baseline inspections, and starts the application (`app/start_app.py`). See `deploy/README.md` for the tasks, environment variables and how to rerun.

The tasks run in the same project, so they share `outputs/inspections/`.

## Storage
Under `outputs/inspections/<inspection_id>/` (not in Git):

| File | Content |
|---|---|
| `result.json` | Inspection result |
| `overlay.jpg` | Saved overlay |
| `masks.npz` | Per-class masks `(6, H, W)` for toggles |
| `reviews.jsonl` | One JSON line per review |

A review belongs to one inspection ID. Re-inspecting an image starts as "Not reviewed".

## Batch Job results
- Baseline: `docs/step1-validation.md` (retained regions per class).
- MATCH count: __ of 29
- Runtime: __

## Known limits
- Inspections made before `masks.npz` existed have no class toggles.
- Reviews are not editable or deletable in the UI.
- Masks and areas are approximate; region counts are mask components, not confirmed defects.
- Guidance is draft only (`draft_pending_review`) and hidden unless `QC_SHOW_DRAFT_GUIDANCE=1`. Nothing is approved for use. Patches has none.
- An image with 3 detected classes uses all 4 agent tool calls (1 inspection plus 3 lookups). Follow-up: one lookup that takes all detected classes. The budget is unchanged.
