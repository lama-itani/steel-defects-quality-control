# Plan: Inspection review UI (drill-down view)

Repository: `lama-itani/steel-defects-quality-control`, branch `main` (last commit checked: `c7032a0`).
Approved design: the "Steel QC Review Mockup" canvas (2 screens: Overview, Image detail).

## Goal

A Streamlit Application in Cloudera AI Workbench that lets a QC engineer:

1. See all 29 held-out test images in an overview grid with a summary and filters.
2. Open one image to see original vs overlay, findings, expected vs detected, limitations and raw JSON.
3. Record a review verdict (Agree / Disagree / Unsure + note), with history.
4. Ask the existing QC agent to explain that inspection (draft shown inline, not saved).

## Rules for Claude Code

- Do not change the model, the endpoint, preprocessing, postprocessing or the agent's control logic.
- Do not commit model files, sample images, generated outputs or credentials.
- Keep the existing `app/readiness.py` and `scripts/start_readiness.py` working.
- Use `unittest`, like the existing tests.
- Show only exception type names in the UI, never raw error text (same pattern as `app/readiness.py`).
- Work in small commits (see the end of this plan). Stop after each phase and show the diff.

## Files to read first (context)

| File | Why |
|---|---|
| `docs/step1-validation.md` | The 29 image names, expected classes and baseline region counts |
| `docs/agent-implementation-status.md` | Current agent status, limits and rules |
| `config/class_mapping.json` | Class IDs and names |
| `src/inspection.py` | How an inspection is run and saved (`result.json`, `overlay.jpg`) |
| `src/qc_tools.py` | `SAMPLES` allowlist, `get_inspection`, inspection-ID validation, storage path |
| `src/qc_agent.py` | `run_agent(prompt)` and its return shape |
| `src/visualization.py` | `create_defect_overlay` (reused for mask toggles) |
| `src/postprocessing.py` | Mask shape `(6, H, W)` |
| `app/readiness.py` | Existing Streamlit patterns (session state, hidden errors, agent call) |
| `scripts/start_readiness.py` | How the Application starts Streamlit (`127.0.0.1`, `CDSW_READONLY_PORT`) |
| `tests/test_qc_agent_controls.py` | Test style; must keep passing |
| `.gitignore` | Confirms `data/*.jpg` and `outputs/` stay out of Git |

---

## Phase 1 — Sample catalog (single source of truth)

**New file: `src/catalog.py`**

- `SAMPLE_FILES`: ordered list of the 29 file names from `docs/step1-validation.md` (Crazing 5, Patches 5, Inclusion 4, Pitted surface 5, Rolled-in scale 5, Scratches 5). Keep it an explicit list, not a folder scan. It is also the agent's allowlist.
- `PREFIX_TO_CLASS`: `crazing` → Crazing, `patches` → Patches, `inclusion` → Inclusion, `pitted_surface` → Pitted surface, `rolled-in_scale` → Rolled-in scale, `scratches` → Scratches.
- `expected_class(file_name) -> str`: take the part before the last `_<number>.jpg`. Raise `ValueError` if unknown.
- `sample_path(file_name) -> Path`: `ROOT / "data" / file_name`. Only for names in `SAMPLE_FILES`.
- Check at import that every `PREFIX_TO_CLASS` value exists in `config/class_mapping.json`.

**Edit: `src/qc_tools.py`**

- Build `SAMPLES` from `catalog.SAMPLE_FILES` (`{name: f"data/{name}"}`). Keep the existing path checks in `inspect_image`.
- Effect: the agent's `inspect_image` enum grows from 2 to 29 values. No change to `src/qc_agent.py` is needed.

**New test: `tests/test_catalog.py`**

- 29 unique names; class counts 5/5/4/5/5/5.
- `expected_class` is correct for one name per class, including `rolled-in_scale_14.jpg` and `pitted_surface_125.jpg`.
- Unknown name raises `ValueError`.
- `qc_tools.SAMPLES` keys equal `catalog.SAMPLE_FILES`.

---

## Phase 2 — Save masks so the UI can toggle classes

The overlay is currently saved as a flat image. To turn single classes on or off, the masks are needed.

**Edit: `src/inspection.py`** (small change only)

- After `postprocess_output`, save the masks: `np.savez_compressed(output_dir / "masks.npz", masks=masks.astype(np.uint8))`.
- No other result fields change. The UI finds the file by inspection ID, so no path is added to `result.json`.

**New function in `src/review_store.py`** (see Phase 3) or `src/catalog.py`:

- `load_masks(inspection_id) -> np.ndarray | None`: validate the ID (same regex as `qc_tools.get_inspection`), load `STORE/<id>/masks.npz`, check shape `(6, H, W)`. Return `None` if the file is missing. Older inspections have no masks.

The UI recomposes the overlay with `visualization.create_defect_overlay(original, masks_with_unchecked_classes_zeroed, mapping)`.

---

## Phase 3 — Review storage and review logic (no Streamlit)

**New file: `src/review_store.py`**

- `STORE = qc_tools.STORE` (reuse; do not define a second path).
- `latest_inspections() -> dict[str, dict]`: scan `STORE/*/result.json` and use `qc_tools.get_inspection(id)` to load each one, so the existing validation applies. Keep the newest `created_at` per `image_id`, only for names in `catalog.SAMPLE_FILES`. Skip invalid folders silently.
- `append_review(inspection_id, verdict, note) -> dict`:
  - `verdict` in `{"agree", "disagree", "unsure"}`, otherwise `ValueError`.
  - `note`: strip; max 2000 characters; required when verdict is `disagree`.
  - Inspection must exist (call `qc_tools.get_inspection`).
  - Append one JSON line to `STORE/<id>/reviews.jsonl`: `{"verdict", "note", "reviewed_at"}` (UTC ISO timestamp). Open in append mode, flush and `os.fsync`.
  - Return the saved record.
- `review_history(inspection_id) -> list[dict]`: read `reviews.jsonl`, skip bad lines, return newest first.
- `latest_review(inspection_id) -> dict | None`.

Reviews belong to an inspection ID. If an image is inspected again, it starts as "Not reviewed". This is intended: the review is about that model result.

**New file: `src/review_logic.py`** (pure functions, easy to test)

- `build_rows(latest, reviews) -> list[dict]`: one row per name in `SAMPLE_FILES`, in catalog order:
  `image_id, expected_class, inspection_id | None, detected_classes, findings, status ("not_inspected" | "not_reviewed" | "agree" | "disagree" | "unsure"), flag`.
- `flag` rules:
  - `None` if detected set == {expected}.
  - `"extra_class"` if expected is detected plus other classes.
  - `"expected_missing"` if expected is not detected but something else is.
  - `"no_detection"` if nothing is detected.
- `filter_rows(rows, class_name=None, mismatch_only=False, status=None)`.
- `summary(rows)`: total, expected detected count, images with a flag, reviewed count.
- `neighbours(filtered_rows, image_id) -> (previous_id, next_id)`.
- `next_unreviewed(filtered_rows, after_image_id=None)`: first row with status `not_reviewed` after the current one, wrapping around; `None` if all are reviewed.

**New tests: `tests/test_review_store.py`, `tests/test_review_logic.py`**

- Use a temporary folder; patch `qc_tools.STORE` and `review_store.STORE`.
- Append/read order; invalid verdict; disagree without note; note too long; invalid or unknown inspection ID.
- Bad JSON line is skipped.
- Flags for: exact match, `patches_274.jpg` case (extra class), expected missing, no detection.
- `next_unreviewed` wraps and returns `None` when all are reviewed.

---

## Phase 4 — Batch inspection Job

**New file: `scripts/run_batch_inspections.py`**

- For each name in `catalog.SAMPLE_FILES`: if the image file is missing, record it and continue; otherwise call `src.inspection.inspect_image(str(catalog.sample_path(name)))`.
- Option `--only-missing`: skip images that already have an inspection in `review_store.latest_inspections()`.
- Print per image: name, detected classes, region counts, endpoint time. At the end print counts of done / missing image / failed.
- Compare against the baseline in `docs/step1-validation.md` for detected classes and retained regions. Store the expected values as a small dict in the script (copied from the doc, not invented). Print `MATCH` / `DIFF` per image.
- Exit code 1 if any inspection failed or differs from the baseline.
- Hide raw error text; print the exception type name only.

Notes:
- One endpoint round trip took about 1.6 s in an earlier test (single observation). 29 images run in sequence, so expect roughly a minute, but measure it.
- The Job must run in the same project as the Application so both use the same `outputs/inspections/` folder.

---

## Phase 5 — Streamlit review app

**New file: `app/review_app.py`**
**New file: `scripts/start_review_app.py`** (copy `scripts/start_readiness.py`, point it at `app/review_app.py`, remove the port diagnostics)

Structure:

- Add the project root to `sys.path` (same as `app/readiness.py`).
- Navigation with `st.query_params`: no `image` → Overview; `?image=<name>` → Detail. Only accept names in `catalog.SAMPLE_FILES`.
- Keep the filter (class, mismatch only, status) in `st.session_state` so "Back to grid" keeps it.
- Load data with a small cached function; clear the cache after saving a review.

**Overview screen**

- Header: "Steel QC · Inspection review", deployment name from the results, "Results are drafts for human review".
- Summary: 4 `st.metric` values from `review_logic.summary` (Images, Expected class detected, Images with a flag, Reviewed).
- Filters: class (`st.pills` or horizontal `st.radio`, with counts), "Mismatch only" checkbox, review status select.
- Button: "Start review: next unreviewed".
- Grid: `st.columns(4)` per row; each card in `st.container(border=True)`:
  - overlay image from `STORE/<id>/overlay.jpg` (resolve by ID, do not trust a stored path),
  - file name, detected classes, region count,
  - flag label (if any) and review status,
  - "Open" button that sets `?image=<name>`.
- Images without an inspection: grey card with "Not inspected – run the batch Job".

**Detail screen**

- Top bar: "Back to grid", "Image N of M · Filter: …", Previous, Next, Next unreviewed (from `review_logic`).
- Left column:
  - Original (from `catalog.sample_path`) and overlay side by side; `st.image(..., channels="BGR")`.
  - One checkbox per detected class. If `masks.npz` exists, rebuild the overlay with only the checked classes. If not, show the saved overlay and a note: "Mask toggles need a new inspection."
  - QC agent: button "Explain this inspection".
    - Prompt: `"Retrieve inspection <inspection_id>. Look up guidance for every returned defect class, then summarize all findings and limitations. State when guidance is unavailable. Include the inspection ID and label the report as a draft for human review."`
    - Validate the ID with the 32-hex regex before building the prompt.
    - Show the result under `st.warning("DRAFT — FOR HUMAN REVIEW")`: status, answer, and the tool results in an expander. Store it in `st.session_state` keyed by inspection ID. Do not save it to disk.
- Right column:
  - Expected vs detected, with the flag message.
  - Findings table: class, retained regions, approximate area %. Caption with the settings from `result["settings"]`.
  - Review form (`st.form`): Agree / Disagree / Unsure radio, note text area, button "Save and go to next unreviewed". On success: call `review_store.append_review`, clear cache, move to `next_unreviewed`. On `ValueError`: show a clear message (e.g. "A note is required for Disagree").
  - History: from `review_history`, newest first (verdict, timestamp, note).
  - Limitations: from `result["limitations"]`.
  - Raw JSON: `st.expander` + `st.json(result)`.

---

## Phase 6 — Cloudera setup (manual, you do this)

1. Check that all 29 images are in the project's `data/` folder in Workbench (only some are confirmed now). They stay out of Git.
2. Pull the approved branch into the Workbench project.
3. Run the unit tests in a session: `python -m unittest discover tests`.
4. Create a Job: script `scripts/run_batch_inspections.py`. Run it once. Check `MATCH` for all 29. Record the runtime.
5. Create a new Application (keep the readiness one): script `scripts/start_review_app.py`.
6. Walk through: overview → filter Patches → open `patches_274.jpg` → toggle Pitted surface → save a Disagree with a note → check it moved to the next unreviewed image → back to grid shows the status → run the agent on one image.

Things not yet verified that may need adjustment:
- That Jobs have the same environment variables (`CDSW_PROJECT_ID`, `CDSW_APIV2_KEY`) and packages (`cmlapi`) as the Application.
- That `st.pills` and `st.query_params` work as expected in the Application runtime (Streamlit 1.64.0 was recorded there).

---

## Phase 7 — Documentation

- New `docs/review-ui.md`: what the app does, how to run the Job and Application, where reviews are stored, Job results (MATCH count, runtime), known limits.
- Update `docs/agent-implementation-status.md`: sample allowlist is now 29 images.
- Update `README.md` "Current status" with one line about the review app.

---

## Suggested commits

1. `Add sample catalog and expand allowlist to 29 images` (Phase 1)
2. `Save per-class masks with each inspection` (Phase 2)
3. `Add review storage and review logic with tests` (Phase 3)
4. `Add batch inspection job with baseline check` (Phase 4)
5. `Add Streamlit review app` (Phase 5)
6. `Document review UI` (Phase 7)

## Done when

- All unit tests pass (existing and new).
- The batch Job reports MATCH for all 29 images.
- The walkthrough in Phase 6, step 6 works in the Application.
- No images, model files, outputs or credentials are added to Git.
