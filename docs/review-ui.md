# Inspection review UI

Streamlit Application for reviewing the model's results on the 29 held-out test images. Results are drafts for human review; the app makes no accept or reject decisions.

## What it does
- **Overview:** summary metrics, class/mismatch/status filters, grid of overlays.
- **Detail:** original vs overlay with per-class toggles, expected vs detected, findings, limitations, raw JSON.
- **Review:** verdict (agree, disagree, unsure) with a note and history. A note is required for disagree (max 2000 characters).
- **Handling guidance:** one expander per detected class, read directly from `config/defect_guidance.json` through `qc_tools.lookup_defect_guidance` (no LLM call). See below.
- **QC agent:** a chat box plus an "Explain this inspection" button. Each question is answered independently (the agent has no memory of earlier turns). Turns are listed newest first, kept in the session only, and not saved.

Flags: `extra_class`, `expected_missing`, `no_detection`. For example, `patches_274.jpg` also detects Pitted surface.

## Handling guidance panel
Shown in the detail view, right column, between Findings and Review.

- A header line gives the document version and approval state. Unless the document is `approved`, it also shows "Draft guidance – not approved for use".
- Each detected class has an expander with a status badge. When content may be shown it lists the definition, typical causes, common handling steps, class-specific handling, and sources as links with section and access note.
- A class without shown guidance reads "No reviewed guidance for this class."
- If the guidance file is missing or invalid, the panel says "Guidance file unavailable" and no class shows guidance.
- Errors show only the exception type name.

Only entries with status `approved` are shown by default. The file is currently `draft_pending_review`, so by default every class reads "No reviewed guidance". To show the drafts for a demo, set the environment variable `QC_SHOW_DRAFT_GUIDANCE=1` on the Application and restart it. Drafts are then shown with a "Draft – pending review" badge and an "Unreviewed draft guidance – not approved for use" warning. Patches has no guidance in either mode. The flag applies to the QC agent as well, which then labels drafts as unreviewed and cites their sources.

## Run
1. Put all 29 images in `data/` (not in Git).
2. Create a Job with `scripts/run_batch_inspections.py` and run it. Use `--only-missing` to resume.
3. Create an Application with `scripts/start_review_app.py`. Keep the readiness Application on `scripts/start_readiness.py`.

The Job and Application must run in the same project so they share `outputs/inspections/`.

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
