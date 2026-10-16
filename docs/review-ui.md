# Inspection review UI

Streamlit Application for reviewing the model's results on the 29 held-out test images. Results are drafts for human review; the app makes no accept or reject decisions.

## What it does
- **Overview:** summary metrics, class/mismatch/status filters, grid of overlays.
- **Detail:** original vs overlay with per-class toggles, expected vs detected, findings, limitations, raw JSON.
- **Review:** verdict (agree, disagree, unsure) with a note and history. A note is required for disagree (max 2000 characters).
- **QC agent:** "Explain this inspection" shows a draft in the session only. It is not saved.

Flags: `extra_class`, `expected_missing`, `no_detection`. For example, `patches_274.jpg` also detects Pitted surface.

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
- Agent guidance is unavailable; no source has been supplied.
