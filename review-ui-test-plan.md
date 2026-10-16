# Workbench test plan (Phases 1-4)

## 1. Setup
1. Pull the branch into the Workbench project (same project as the model deployment).
2. Confirm all 29 images are in `data/` (`ls data/*.jpg | wc -l` gives 29).
3. Open a session with the same environment the Application uses.

## 2. Unit tests
```
python -m unittest discover tests
```
Expected: all pass, none skipped (`cmlapi`, `requests`, `openai` are available).
- Check that `test_qc_agent_controls` still passes.
- Check that `test_qc_tools_samples_match` is not skipped.

## 3. Single inspection and masks
```
python -c "from src.inspection import inspect_image as i; r=i('data/patches_274.jpg'); print(r['inspection_id'], r['findings'])"
ls outputs/inspections/<inspection_id>
```
Expected: the folder has `result.json`, `overlay.jpg` and `masks.npz`. Findings show Patches 1 and Pitted surface 1.

## 4. Mask loading
```
python -c "from src.review_store import load_masks as l; m=l('<inspection_id>'); print(m.shape, m.dtype)"
```
Expected: `(6, H, W) uint8`.

## 5. Batch Job
1. Create a Job with script `scripts/run_batch_inspections.py`, or run it in the session.
2. Run it and record the total runtime.

Expected:
- 29 lines ending in `MATCH`.
- Final line: `done 29, missing image 0, failed 0, diff 0`.
- Exit code 0.
- No raw error text. Failures show only an exception type name.

## 6. Resume option
Run again with `--only-missing`.
Expected: all 29 lines show `SKIP`, and the final line has `done 0`.

## 7. Review storage
```
python - <<'EOF'
from src import review_store as s
iid = list(s.latest_inspections().values())[0]["inspection_id"]
s.append_review(iid, "unsure", "test")
s.append_review(iid, "agree", "")
print(s.review_history(iid))
try: s.append_review(iid, "disagree", "")
except ValueError as e: print("rejected:", e)
EOF
```
Expected:
- History is newest first (`agree`, then `unsure`).
- Disagree without a note is rejected.
- The folder has `reviews.jsonl`.

## 8. Review app: start
1. Create an Application with script `scripts/start_review_app.py` (keep the readiness one).
2. Open it. Expected: the overview loads with no error.
3. Note the Streamlit version. Expected: `st.pills` and `st.query_params` work.

## 9. Overview
Run this after the batch Job, with step 7 test reviews removed.
- Header shows the deployment name and "Results are drafts for human review".
- Metrics: Images 29, Expected class detected 29, Images with a flag 1 (`patches_274.jpg`), Reviewed 0.
- Grid shows 29 cards with overlay, file name, detected classes, region count and status.
- Class pills show counts 5/5/4/5/5/5, and All (29).
- Click Patches: grid shows 5 cards. Deselect it: grid shows all 29 again.
- "Mismatch only": grid shows only `patches_274.jpg`, flagged "Extra class detected".
- Review status filter: "Not reviewed" shows 29; "Agree" shows 0.
- Remove one image from `data/` and its inspection: that card shows "Not inspected – run the batch Job". Restore it afterwards.

## 10. Detail view
Open `patches_274.jpg`.
- Original and overlay appear side by side.
- Expected Patches; detected Patches and Pitted surface; flag message shown.
- Findings table: Patches 1 region, Pitted surface 1 region, with area %.
- Settings caption: threshold 0.5, min region 200 px at [128, 128].
- Limitations and Raw JSON expanders open and match `result.json`.
- Counter reads "Image N of M" and shows the active filter.

## 11. Mask toggles
- Uncheck Pitted surface: the overlay shows only Patches, with no Pitted surface label or colour.
- Uncheck both: the overlay is the plain image.
- Re-check both: the overlay matches the saved `overlay.jpg`.
- Older inspection without `masks.npz`: shows "Mask toggles need a new inspection" and the saved overlay.

## 12. Navigation
- Next and Previous move in grid order; Previous is disabled on the first image and Next on the last.
- With the Patches filter on, Next stays within Patches.
- "Back to grid" keeps the filter.
- "Next unreviewed" jumps to the next image with no review and wraps around.
- Edit the URL to `?image=nonexistent.jpg`: the overview shows, with no error.
- Browser refresh on a detail page keeps the same image.

## 13. Review form
On `patches_274.jpg`:
- Save with no verdict chosen: "Choose a verdict".
- Disagree with an empty note: "A note is required for Disagree".
- Disagree with a note: saves, then jumps to the next unreviewed image.
- Return to `patches_274.jpg`: history shows the entry (verdict, time, note).
- Save a second review (Unsure): history shows both, newest first.
- Grid status now shows the latest verdict and the Reviewed metric increases.
- Note longer than 2000 characters cannot be entered.
- Review every remaining image: after the last one, the app returns to the grid with "Nothing left to review".
- "Start review: next unreviewed" with all reviewed shows "Nothing left to review in this filter".

## 14. QC agent
- Click "Explain this inspection" on one image. Expected: DRAFT warning, status, answer citing the inspection ID, and the tool results in an expander.
- The answer covers every finding, including Pitted surface for `patches_274.jpg`, and states that guidance is unavailable.
- Open another image and come back: the answer is still shown (session only).
- Reload the page: the answer is gone, and nothing was written to `outputs/`.
- Agent unavailable (for example `/tmp/jwt` missing): shows an error status with an exception type name, and the rest of the page still works.

## 15. Error handling
- No raw error text appears anywhere in the UI, only exception type names.
- Rename one `result.json` to invalid JSON: that card shows as not inspected and the app does not crash. Restore it afterwards.

## 16. Existing behaviour
- `git status` shows no images, `outputs/` or model files.
- The readiness app still starts and its two original samples still inspect.
- Readiness sample labels for all 29 images still work.
- `python -m unittest discover tests` still passes.

## 17. Handling guidance
Guidance comes from `config/defect_guidance.json` (status `draft_pending_review`). Set `QC_SHOW_DRAFT_GUIDANCE=1` in the Application's environment variables and restart it to switch the flag on.

Flag off (variable unset):
- Open `patches_274.jpg`. The right column shows "Handling guidance" with the document version, approval state `draft_pending_review` and the warning "Draft guidance – not approved for use".
- Patches and Pitted surface each have an expander reading "No reviewed guidance for this class."
- Click "Explain this inspection". The answer states that guidance is unavailable for both classes and gives no handling advice.

Flag on:
- Open `patches_274.jpg`. The "not approved" warning is still shown.
- Pitted surface shows a "Draft – pending review" badge, the warning "Unreviewed draft guidance – not approved for use", definition, typical causes, the six common steps, class-specific handling, and sources as links with section and access note.
- Patches still reads "No reviewed guidance for this class."
- Click "Explain this inspection". The answer calls the Pitted surface guidance unreviewed draft guidance, cites its sources, does not call it approved, and states that Patches has none.
- Open a Crazing image. The causes list reads "None recorded" (the file has no causes for Crazing).

Fallback:
- Rename `config/defect_guidance.json`, restart the Application. The panel shows "Guidance file unavailable" and no class shows guidance, even with the flag on. Restore the file afterwards.
- No raw error text appears in any case.

Three detected classes: the agent has a budget of 4 tool calls (1 inspection plus 3 lookups). Expect it to have no calls left for anything else. This is a known limit, not a failure.

## Record
| Item | Result |
|---|---|
| Unit tests | |
| `masks.npz` written | |
| Batch MATCH count (of 29) | |
| Batch runtime | |
| `--only-missing` | |
| Review storage | |
| Streamlit version, pills and query params | |
| Overview metrics and filters | |
| Detail view | |
| Mask toggles | |
| Navigation | |
| Review form and history | |
| QC agent | |
| Handling guidance, flag off and on | |
| Error handling | |
| Readiness app | |
| Issues found | |

## Cleanup
- Step 7 test reviews stay in `outputs/`. Delete `reviews.jsonl` from that inspection folder before real review.
- Restore anything renamed or removed in steps 9 and 15.
- Delete test reviews from steps 13 and 14 if the real review should start from zero.
