# Plan: QC dashboard, inspection record download, sensitivity what-if

For Claude Code, working in `lama-itani/steel-defects-quality-control` (`main`).

## Goal
Add three features to the review app (`app/review_app.py`). Each fills a real QC role the app does not cover yet:

1. **QC dashboard**: a supervisor's overview: defect Pareto, area bands, model vs expected class, model vs reviewer, attention list.
2. **Inspection record download**: a traceable, printable record of one inspection and its reviews.
3. **Sensitivity what-if**: an engineer's view of how threshold and minimum region size change the result for one image.

Time budget: about 2 hours in total. Build the parts in order. If time runs out, drop Part 3; do not rush it.

## Rules for you (Claude Code)
- Work on a new branch `feature/qc-insights`. One commit per part, plus one for docs. **Do not push. Do not open a PR.**
- Do not change the model, `src/inspection.py`, preprocessing, postprocessing, `src/visualization.py`, the result JSON, the agent, `scripts/run_batch_inspections.py` or its `BASELINE`.
- Do not add dependencies. Use Streamlit, NumPy, OpenCV and pandas (installed with Streamlit) only.
- Nothing new is written to `outputs/`. The what-if is never saved.
- Show only exception type names in the UI, never raw error text (existing pattern).
- Use `unittest`, like the existing tests. Put pure logic in `src/` so it can be tested without Streamlit.
- Never call any output a certificate, release, acceptance or rejection. Results stay drafts for human review.
- If something is unclear or a check fails, **stop and ask me**. Do not guess.

## Files to read first
| File | Why |
|---|---|
| `app/review_app.py` | Routing (`?image=`), `go()`, `NAV_CSS` (`nav_` keys), `overview()`, `detail()`, `overlay_file()`, `class_hex()` |
| `src/review_logic.py` | `build_rows` row shape (`image_id`, `expected_class`, `inspection_id`, `detected_classes`, `findings`, `status`, `flag`) |
| `src/review_store.py` | `STORE`, `review_history`, `load_masks` |
| `src/inspection.py` | `_get_model()`, how findings and area % are computed |
| `src/postprocessing.py` | `postprocess_output(logits, original_shape, threshold, min_size)` |
| `src/preprocessing.py` | `preprocess_image(path) -> (tensor, original)` |
| `tests/test_review_logic.py` | Test style |

---

## Part 1: QC dashboard (~45 min)

### 1a. `src/review_logic.py`: add `dashboard_stats(rows) -> dict`
Pure function, no Streamlit. Input is the output of `build_rows`. Only rows with an `inspection_id` count as inspected.

Return:
- `pareto`: list of `{"class_name", "images", "regions"}` for every **detected** class: the number of inspected images where it appears, and the sum of `retained_regions`. Sort by `images` then `regions`, descending. Classes with zero images are left out.
- `area_bands`: for each class in `catalog.PREFIX_TO_CLASS.values()` order, counts of findings by `approximate_mask_area_percent`: `"<5%"` (< 5), `"5–20%"` (5 to < 20), `"≥20%"` (≥ 20).
- `per_class`: for each class (catalog order), grouped by **expected** class: `images`, `inspected`, `expected_detected`, `detection_rate` (`expected_detected / inspected`, `None` if 0 inspected), and verdict counts `agree`, `disagree`, `unsure`, `not_reviewed`.
- `attention`: `image_id`s of rows with a `flag` or status `disagree`, in catalog order.

### 1b. Tests: `tests/test_review_logic.py`, new class `DashboardTests`
Build rows by hand (do not use real inspection files):
- Pareto order and counts with two classes, including one image that detects two classes.
- Area band boundaries: 4.99 → `<5%`, 5.0 → `5–20%`, 20.0 → `≥20%`.
- `detection_rate` is `None` when nothing is inspected; the verdict counts add up to `inspected`.
- `attention` includes a flagged row and a `disagree` row, and excludes an `agree` row with no flag.
- `rl.build_rows({}, {})` gives an empty `pareto` and an empty `attention`.

### 1c. `app/review_app.py`: dashboard view
- Routing: `?view=dashboard` shows the dashboard. Keep the order: a valid `?image=` → detail; else `view == "dashboard"` → dashboard; else overview. Add `go_view(view)`, which clears the query params and then sets `view`. `go()` stays unchanged, so "Back to grid" from the detail page still works.
- Overview: add a "QC dashboard" button next to the title, with key `nav_dashboard` so it gets the dark blue `NAV_CSS` style.
- New function `dashboard(rows)`:
  - Top bar: "Back to grid" (`key="nav_back_dash"`, `on_click=go`).
  - Title "Steel QC · Dashboard" and the caption: "Figures cover the sample images only and do not describe production quality. Areas are approximate. Results are drafts for human review."
  - Metrics row: reuse `rl.summary(rows)` (the same 4 metrics as the overview).
  - **Defect Pareto**: `st.bar_chart` of `images` per detected class (sorted), with a `st.dataframe` beside it showing images and regions.
  - **Affected-area bands**: stacked `st.bar_chart` with class on x and the three bands as series. Call it "area band", never "severity".
  - **Model vs expected class**: `st.dataframe` with class, inspected, expected detected, detection rate (as %). Caption: "Expected class comes from the file name."
  - **Reviewer verdicts**: stacked `st.bar_chart` of agree / disagree / unsure / not reviewed per expected class. Caption with the overall agree share of reviewed images, or "No reviews yet".
  - **Needs attention**: one line per `attention` image with file name, flag label (`FLAG_LABEL`), status (`STATUS_LABEL`) and an "Open" button (`on_click=go, args=(image_id,)`). If empty: "Nothing flagged or disagreed."
- If no image is inspected, show `st.info("No inspections yet – run the batch Job")` and stop.

Commit: `Add QC dashboard with defect Pareto and review agreement`

---

## Part 2: Inspection record download (~35 min)

### 2a. New `src/report.py`
`build_record_html(result, history, expected_class, flag_label, original_bgr, overlay_bgr) -> str`

- Returns one self-contained HTML page with no external resources. Images are embedded as base64 PNG via `cv2.imencode(".png", ...)`. If an image is `None`, show "Image unavailable".
- **Escape every text value with `html.escape`**, especially review notes, which are user input.
- Content, in this order:
  1. Banner: "DRAFT – FOR HUMAN REVIEW. This record does not accept or reject material."
  2. Title "Steel surface inspection record" and `image_id`.
  3. Traceability table: inspection ID, created at, deployment, model version (`"not recorded"` if `None`), probability threshold, minimum region, region filter resolution, inference ms, record generated at (UTC now, ISO).
  4. Original and overlay side by side.
  5. Expected class, detected classes, flag label (or "None").
  6. Findings table: class, retained regions, approximate area %. If none: "No retained detections. This does not mean defect-free."
  7. Review history, newest first: verdict, time, note. If none: "Not reviewed."
  8. Limitations from `result["limitations"]`.
- Inline CSS only, readable when printed (`@media print`: no background colours except the banner border; avoid page breaks inside tables).

### 2b. Test: new `tests/test_report.py`
Use small `np.zeros((10, 10, 3), np.uint8)` images and a hand-made result dict:
- The output contains the inspection ID, the DRAFT banner, each finding's class name and `data:image/png;base64,`.
- A note `<script>alert(1)</script>` appears escaped (`&lt;script&gt;`) and never raw.
- `model_version: None` renders "not recorded".
- `original_bgr=None` renders "Image unavailable" and does not raise.
- No findings renders the "does not mean defect-free" sentence.

### 2c. `app/review_app.py`: button on the detail page
- In the right column, under the review history, add `st.download_button("Download inspection record", ...)`.
- Data: `build_record_html(result, rs.review_history(iid), row["expected_class"], FLAG_LABEL.get(row["flag"]), original, saved_overlay)`. `saved_overlay = cv2.imread(overlay_file(iid))` when the file exists, else `None`. Use the **saved** overlay, not the toggled view.
- File name: `inspection-record_<image stem>_<iid[:8]>.html`, mime `text/html`.
- Caption: "Open the file and use your browser's Print to save it as PDF."
- Wrap the build in `try/except` and show `Record unavailable (<ExceptionType>)` on failure.

Commit: `Add downloadable inspection record`

---

## Part 3: Sensitivity what-if (~40 min)

### 3a. New `src/what_if.py`
- `compute_logits(image_path) -> tuple[np.ndarray, np.ndarray]`: `preprocess_image(path)` then `inspection._get_model().predict(tensor)`. Return `(logits, original)`. Check that the shape is `(1, 6, 128, 128)` and that all values are finite (same checks as `inspection.py`).
- `findings_at(logits, original_shape, threshold, min_size, mapping) -> tuple[masks, findings]`: call `postprocess_output(logits, original_shape, threshold=threshold, min_size=min_size)` and build findings **exactly** like `src/inspection.py` (same keys, same `round(100 * count_nonzero / size, 2)`). Do not refactor `inspection.py` to share the code.
- `diff_findings(base, new) -> list[dict]`: one row per class present in either list: `class_name`, `regions_recorded`, `regions_what_if`, `area_recorded`, `area_what_if`, `change` (`"added"`, `"removed"`, `"changed"`, `"same"`).

### 3b. Test: new `tests/test_what_if.py`
No model needed. Build logits `np.full((1, 6, 128, 128), -10, np.float32)` and set a 20×20 block in channel 2 (400 px):
- Block value `0.5` (sigmoid ≈ 0.62): found at `threshold=0.5`, gone at `threshold=0.7`.
- Block value `5`: found at `min_size=200`, gone at `min_size=500`.
- The findings keys are equal to the keys `inspection.py` writes.
- `diff_findings`: one added, one removed, one changed and one same case.

### 3c. `app/review_app.py`: what-if expander on the detail page
- In the left column, under the images and class toggles, add `st.expander("What-if: sensitivity settings")`.
- Cache logits per image name with `@st.cache_data(max_entries=32)` around `what_if.compute_logits(catalog.sample_path(image))`. The model runs once per image; slider moves only redo postprocessing.
- Sliders: probability threshold 0.30–0.80, step 0.05, default 0.50; minimum region (px at 128×128) 50–500, step 25, default 200. Use keys scoped by image so each image starts at the defaults.
- Show the what-if overlay (`create_defect_overlay(original, masks, MAPPING)`, `channels="BGR"`) next to the saved overlay, then the `diff_findings` table against `result["findings"]`.
- Warning above the sliders: "Exploration only – not the recorded inspection. Nothing is saved."
- When the sliders are at the defaults, show a caption: "At the recorded settings" and the diff must be all `same`.
- On any exception, show `What-if unavailable (<ExceptionType>)`. The rest of the page must keep working.

Commit: `Add sensitivity what-if on the detail page`

---

## Docs
- `docs/review-ui.md`, "What it does": add three bullets (Dashboard, Inspection record, What-if) with one line each.
- "Known limits", add:
  - "Dashboard figures cover the sample images only."
  - "The inspection record is a draft, not a certificate or material release."
  - "What-if results are not saved and do not change the recorded inspection or baseline."
- `docs/agent-implementation-status.md`: change "report download remain unfinished" to say that a human-readable inspection record download exists in the review app, and that the agent tool `create_inspection_report` is still not implemented.

Commit: `Document dashboard, inspection record and what-if`

## Checks before you hand back
1. `python -m unittest discover tests`: all pass, with the new tests included. Say which tests were skipped and why.
2. `python scripts/run_batch_inspections.py`: still `diff 0`. This proves nothing in the inspection path changed. If `cmlapi` or the model is unavailable locally, say so.
3. `git diff main --stat`: no changes to `src/inspection.py`, `src/postprocessing.py`, `src/preprocessing.py`, `src/visualization.py`, `src/qc_agent.py`, `scripts/run_batch_inspections.py` or `requirements.txt`.
4. Start the app locally and walk through:
   - Overview → "QC dashboard": all five sections render, "Back to grid" works, and "Open" on an attention item opens that image.
   - Open `rolled-in_scale_4.jpg`: download the record, open it in a browser, check the images, the extra-class flag, the review history and the DRAFT banner. Print preview fits on A4.
   - Save a Disagree review with the note `<b>test</b>`: the record shows the tags as text, and the dashboard counts the disagree and lists the image under attention.
   - What-if on `rolled-in_scale_4.jpg`: defaults show all `same`; raising the threshold or minimum region changes the table; moving to another image resets the sliders.
   - Nothing new appears under `outputs/inspections/` after using the what-if.
5. Give me: a summary of changes, the commit list, and anything you could not verify.

## Out of scope
- Automatic disposition (accept, rework, downgrade) or any severity grading.
- Invented coil, shift or line metadata, or time trends.
- An agent tool for reports, PDF libraries, and saving what-if results.
