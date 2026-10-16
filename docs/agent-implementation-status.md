# Steel QC agent implementation checkpoint

Date: 2026-09-25
Status: Application readiness verified; Stage 2 partially implemented.

## Architecture

The eight-hour implementation plan supersedes the two-day plan:
Streamlit in a Cloudera AI Workbench Application, one Python
tool-calling agent, and Jobs for setup and validation. No Agent Studio.

## Verified

- The Application starts with project-root resolution via Path.cwd().
- Streamlit binds to 127.0.0.1 using CDSW_READONLY_PORT.
- Application runtime: Python 3.10.20, streamlit 1.64.0,
  openai 3.19.2, cmlapi 26.8.4, numpy 2.2.6, requests 2.32.5.
- Both the existing inspection endpoint and a harmless Qwen tool-calling
  round trip succeeded from inside the Application.
- Readiness endpoint calls are button-triggered.
- Scratches baseline matched: 3 retained regions, 17.83% approximate area.
- Repeated inspections save separate JSON results and overlays under
  outputs/inspections/<inspection_id>/ without overwriting earlier results.
- Saved-result retrieval, invalid sample arguments, invalid/unknown
  inspection IDs, and missing guidance checks passed.
- A terminal agent test retrieved a saved Scratches inspection and checked
  Scratches guidance in two tool calls. Its summary matched the result.

## Implemented, with validation still pending

- Three registered tools: inspect_image, get_inspection,
  lookup_defect_guidance.
- Sample allowlist: scratches_86.jpg and patches_274.jpg.
- Argument validation, LLM request timeout, and four-tool-call budget.
- Guidance requests restricted to classes in the latest successful
  inspection or retrieval.

An initial agent test incorrectly requested Patches guidance for a
Scratches inspection. A Python context check was added. The subsequent
test selected Scratches correctly; deliberate mismatch rejection still
needs testing.

## Remaining Stage 2 checks

- Agent-driven inspection and saved-result retrieval.
- Patches example: preserve both Patches and Pitted surface if returned.
- Unknown tools, malformed tool arguments, and call-limit enforcement.
- Deliberate guidance-class mismatch rejection.
- LLM failure after a successful tool call preserves tool results.
- Full agent execution from the Application runtime.

## Limitations and deferred work

No guidance has been approved. A draft guidance file now exists; see
"Defect guidance file" below. By default tools still return "guidance
unavailable" with no invented source or version.

Reports are drafts for human review. Masks and areas are approximate;
training masks came from bounding boxes. Region counts are mask
components, not confirmed defects. This six-class detector is not
general anomaly detection. No detections does not mean defect-free.
Probabilities are not calibrated confidence. No automatic material
acceptance, rejection, or external actions are authorized.

The full UI, setup/validation Jobs, dependency packaging, project
metadata, and report download remain unfinished. Final runtime edition
has not been verified.

Repository visibility and model/sample reuse rights remain unresolved.
This checkpoint must not add model files, sample images, generated
outputs, credentials, or the exploratory notebook.
## Stage 2 validated — 2026-09-25

- Full agent succeeded inside the Workbench Application.
- Patches test: three successful tool calls; Patches (1 region, 13.14%)
  and Pitted surface (1 region, 1.51%). Both guidance lookups unavailable.
- Draft label and tool evidence displayed explicitly.
- Tool availability now follows inspection context; guidance class enum
  is restricted to returned findings.
- Oversized batches remain rejected, with diagnostic tool names/count.
- All five mocked control tests pass after the changes.
- Next: user interface, report persistence/download, Jobs and packaging.

## Review UI — sample allowlist expanded

- The agent's `inspect_image` allowlist is now the 29 images in
  `src/catalog.py` (previously `scratches_86.jpg` and `patches_274.jpg`).
- Review app, batch Job and storage: see `docs/review-ui.md`.

## Defect guidance file — 2026-10-16

- `config/defect_guidance.json` holds handling guidance per class, drawn
  from public sources (EN 10163 via SCI GN 3.05, VDEh atlas, Jansto 2012).
  Document status is `draft_pending_review`; nothing is approved. Five
  classes are drafts; Patches is `guidance unavailable`.
- `lookup_defect_guidance` loads and validates the file once. Class keys must
  match `class_mapping.json` and every source ID must exist. A missing or
  invalid file makes every class return "guidance unavailable".
- Only `approved` entries are returned by default. Drafts are returned as
  "guidance unavailable" unless `QC_SHOW_DRAFT_GUIDANCE=1` is set, in which
  case they carry `status: "draft_pending_review"`.
- Return keys are unchanged: `defect_class`, `status`, `guidance`, `source`,
  `version`.
- The `SYSTEM` prompt and the two app prompts now tell the agent to label
  draft guidance as unreviewed, cite its sources, and state which classes
  have none. Model, endpoint, tool budget, `active_classes` and dispatch
  validation are unchanged.
- The review UI shows the guidance directly, without the agent; see
  `docs/review-ui.md`.
- Gaps left as they are in the file: no typical causes for Crazing, no
  content for Patches, placeholder document ID, no owner or approver, and
  process actions for Rolled-in scale and Scratches still to be added by a
  reviewer. Class mappings for Inclusion and Pitted surface have low
  confidence.
- The tool description still reads "Check for reviewed local defect
  guidance"; it was left unchanged.

### Known limit

An image with 3 detected classes uses all 4 tool calls (1 inspection plus
3 lookups), leaving none spare. Not fixed. Follow-up: a single lookup that
takes all detected classes. The budget of 4 is unchanged.
