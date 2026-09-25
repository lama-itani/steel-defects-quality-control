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

Guidance has not been supplied; tools return "guidance unavailable"
with no invented source or version.

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
