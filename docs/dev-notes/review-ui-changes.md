# Review UI: changes (Phases 1-5, 7)

Phases 1-4 were merged with `origin/main` at c7032a0. Phase 5 is committed on `start_review_app` (16a573f). Phase 7 docs are uncommitted. Phase 6 is the manual Cloudera setup.

## Phase 1: Sample catalog
- New `src/catalog.py`: `SAMPLE_FILES` (29 names), `PREFIX_TO_CLASS`, `expected_class()`, `sample_path()`. Checks class names against `config/class_mapping.json` at import.
- Edit `src/qc_tools.py`: `SAMPLES` is built from `SAMPLE_FILES`. The agent's `inspect_image` allowlist grows from 2 to 29 images.
- New `tests/test_catalog.py`.

## Phase 2: Masks saved
- Edit `src/inspection.py`: writes `masks.npz` (uint8, shape `(6, H, W)`) next to `overlay.jpg`. `result.json` is unchanged.
- `load_masks()` in `src/review_store.py`: validates the ID and shape; returns `None` for older inspections.

## Phase 3: Review storage and logic
- New `src/review_store.py`: `latest_inspections`, `append_review`, `review_history`, `latest_review`. Reviews are appended to `<inspection>/reviews.jsonl`.
- New `src/review_logic.py`: `build_rows`, `filter_rows`, `summary`, `neighbours`, `next_unreviewed`. No Streamlit dependency.
- Rules: verdict is agree, disagree or unsure. A note is required for disagree, max 2000 characters.
- New `tests/test_review_store.py`, `tests/test_review_logic.py`.

## Phase 4: Batch Job
- New `scripts/run_batch_inspections.py`: inspects all 29 images, compares region counts to the baseline in `docs/step1-validation.md`, prints `MATCH` or `DIFF`. `--only-missing` skips images that already have an inspection. Exit code 1 on any failure or diff.

## Phase 5: Review app
- New `app/review_app.py`: overview (metrics, filters, grid) and detail (class toggles, findings, review form, history, agent draft, raw JSON). Navigation uses `?image=<name>`, limited to catalog names. Only exception type names are shown.
- New `scripts/start_review_app.py`: launches the app on `127.0.0.1` and `CDSW_READONLY_PORT`.

## Phase 7: Documentation
- New `docs/review-ui.md`: usage, storage, Job results (to fill in), known limits.
- Edit `docs/agent-implementation-status.md`: allowlist is now 29 images.
- Edit `README.md`: one status line for the review app.

## Other
- `.gitignore`: added `review-ui-plan.md` (kept upstream additions).

## Not changed
Model, endpoint, preprocessing, postprocessing, agent logic, `app/readiness.py`, `scripts/start_readiness.py`.

## Open items
- Fill in the Job MATCH count and runtime in `docs/review-ui.md`.
- Complete `review-ui-test-plan.md` (steps 8-16) in Workbench before the PR.
