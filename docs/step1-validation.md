# Step 1 — ONNX Model Validation

## Current status
**2026-09-24**
Local and Cloudera CPU validation are complete. Deployed endpoint inspection now works on three known images through src/inspection.py. LLM integration is next; see the dated validation sections below.

## Environment
- Date: 2026-09-16
- Operating system: macOS 26.6.2
- Machine: MacBook Pro (Mac15,7)
- Processor: Apple M3 Pro, 12 cores
- Memory: 36 GB
- Python: 3.10.21
- ONNX: 1.22.0
- ONNX Runtime: 1.23.2
- NumPy: 2.2.6
- OpenCV: 5.0.0
- Execution provider: CPUExecutionProvider

## Model contract
- Input: `[1, 3, 128, 128]`, FP32
- Output: `[1, 6, 128, 128]`, FP32
- Output values are finite
- Contract tests: 2 passed

## Initial image test
- Image: `crazing_241.jpg`
- Expected category: Crazing
- Detected category: Crazing
- Retained regions: 1
- Other channels activated: None
- CPU inference time: 21.98 ms
- Overlay generated successfully

The mask covers a large connected region. Detailed boundary accuracy has not yet been assessed against the annotation.

## Phase 2 — Prediction-quality validation
### Crazing — completed
| Image | Detected category | Retained regions | False class activations | Visual assessment | CPU inference |
|---|---|---:|---|---|---:|
| `crazing_151.jpg` | Crazing | 1 | None | Partial overlap; possible missed area | 26.82 ms |
| `crazing_153.jpg` | Crazing | 1 | None | Good but partial overlap | 23.43 ms |
| `crazing_166.jpg` | Crazing | 3 | None | Relevant areas detected; localization fragmented | 22.57 ms |
| `crazing_240.jpg` | Crazing | 1 | None | Broad, coarse localization | 23.30 ms |
| `crazing_241.jpg` | Crazing | 1 | None | Broad, coarse localization | 22.20 ms |

- Correct Crazing activation: 5/5
- False class activations: 0
- Average CPU inference time: 23.66 ms
- Localization quality: Mixed; masks can be partial, fragmented or overly broad.
- Category decision: Usable for category-level detection. Precise segmentation accuracy is not yet established.

### Patches — completed
| Image | Detected categories | Retained regions | False class activations | Visual assessment | CPU inference |
|---|---|---:|---|---|---:|
| `patches_28.jpg` | Patches | Patches: 3 | None | Good overlap with three visible patch regions | 23.94 ms |
| `patches_63.jpg` | Patches | Patches: 1 | None | Good overlap with the main visible patch | 22.60 ms |
| `patches_128.jpg` | Patches | Patches: 2 | None | Good overlap with two visible patch regions | 29.53 ms |
| `patches_151.jpg` | Patches | Patches: 2 | None | Good overlap; boundaries are broad | 24.31 ms |
| `patches_274.jpg` | Patches, Pitted surface | Patches: 1; Pitted surface: 1 | Pitted surface | Patch localization is partial; small probable false positive | 23.14 ms |

- Correct Patches activation: 5/5
- False class activations: 1/5 images
- False activation: One Pitted surface region on `patches_274.jpg`
- Average CPU inference time: 24.70 ms
- Localization quality: Good overall; `patches_274.jpg` is partial.
- Category decision: Usable for category-level detection. Monitor cross-class false activations.

### Inclusion — completed
| Image | Detected category | Retained regions | False class activations | Visual assessment | CPU inference |
|---|---|---:|---|---|---:|
| `inclusion_161.jpg` | Inclusion | 1 | None | Correct area; broad boundary | 64.60 ms initial; 23.31 and 23.01 ms repeated |
| `inclusion_169.jpg` | Inclusion | 2 | None | Good overlap with both visible regions | 26.15 ms |
| `inclusion_195.jpg` | Inclusion | 1 | None | Good overlap with the faint central defect | 25.70 ms |
| `inclusion_263.jpg` | Inclusion | 1 | None | Good overlap; slightly broad boundary | 25.64 ms |

- Correct Inclusion activation: 4/4
- False class activations: 0
- Typical CPU inference range: 23.01–26.15 ms
- Representative average: 25.16 ms, using the repeated average for `inclusion_161.jpg`
- Timing note: The initial 64.60 ms result was not reproduced.
- Localization quality: Good overall, with broad boundaries on some images.
- Category decision: Usable for category detection and approximate localization.

### Pitted surface — completed
| Image | Detected category | Retained regions | False class activations | Visual assessment | CPU inference |
|---|---|---:|---|---|---:|
| `pitted_surface_18.jpg` | Pitted surface | 1 | None | Broad coverage of distributed pitting | 24.75 ms |
| `pitted_surface_64.jpg` | Pitted surface | 1 | None | Broad coverage of distributed pitting | 27.25 ms |
| `pitted_surface_110.jpg` | Pitted surface | 1 | None | Broad coverage of distributed pitting | 22.52 ms |
| `pitted_surface_125.jpg` | Pitted surface | 2 | None | Partial coverage; mainly upper regions detected | 21.78 ms |
| `pitted_surface_175.jpg` | Pitted surface | 1 | None | Broad coverage of dense pitting | 24.28 ms |

- Correct Pitted surface activation: 5/5
- False class activations: 0
- Average CPU inference time: 24.12 ms
- Localization quality: Coarse and broad; `pitted_surface_125.jpg` is partial.
- Category decision: Usable for category detection, but not precise individual-pit localization.

### Rolled-in scale — completed
| Image | Detected category | Retained regions | False class activations | Visual assessment | CPU inference |
|---|---|---:|---|---|---:|
| `rolled-in_scale_14.jpg` | Rolled-in scale | 1 | None | Good overlap with the vertical defect chain; broad boundary | 55.67 ms initial; 21.07–23.55 ms stable repeats |
| `rolled-in_scale_80.jpg` | Rolled-in scale | 1 | None | Broad coverage of the main right-side defect band | 23.78 ms |
| `rolled-in_scale_138.jpg` | Rolled-in scale | 1 | None | Main central defect cluster detected | 23.75 ms |
| `rolled-in_scale_176.jpg` | Rolled-in scale | 1 | None | Main cluster detected; possible isolated misses | 22.77 ms |
| `rolled-in_scale_216.jpg` | Rolled-in scale | 1 | None | Broad coverage of the diagonal defect cluster | 22.89 ms |

- Correct Rolled-in scale activation: 5/5
- False class activations: 0
- Stable CPU inference range: 21.07–23.78 ms
- Representative average: 23.13 ms, using the stable repeated average for `rolled-in_scale_14.jpg`
- Timing note: Transient warm-up readings between 34.90 and 73.59 ms were also observed.
- Localization quality: Good approximate localization, with broad boundaries.
- Category decision: Usable for category detection and approximate localization.

### Scratches — completed

| Image | Detected category | Retained regions | False class activations | Visual assessment | CPU inference |
|---|---|---:|---|---|---:|
| `scratches_86.jpg` | Scratches | 3 | None | Three prominent scratches detected; possible faint miss | 26.18 ms |
| `scratches_195.jpg` | Scratches | 1 | None | Main scratch detected; possible thin secondary miss | 24.29 ms |
| `scratches_264.jpg` | Scratches | 1 | None | Multiple scratches merged into one broad region | 23.68 ms |
| `scratches_286.jpg` | Scratches | 1 | None | Good overlap with the main horizontal scratch | 28.32 ms |
| `scratches_300.jpg` | Scratches | 1 | None | Upper scratches detected as one merged region | 24.54 ms |

- Correct Scratches activation: 5/5
- False class activations: 0
- Average CPU inference time: 25.40 ms
- Localization quality: Good approximate localization; some scratches are merged or possibly missed.
- Category decision: Usable for category detection and approximate localization.

### Phase 2 summary

- Held-out images assessed: 29
- Expected category activated: 29/29
- Images with a false class activation: 1/29
- False activation: Pitted surface on `patches_274.jpg`
- Stable CPU inference was generally between 21 and 30 ms.
- Localization is approximate. Masks can be broad, fragmented, merged or partial.
- Precise segmentation accuracy is not established because the training annotations use bounding boxes.

## Phase 3 — Cloudera AI CPU validation

### Environment

- Cloudera AI Workbench
- Runtime: JupyterLab, Python 3.10, Standard edition 2026.08
- Resources: 2 vCPU, 4 GiB memory
- Spark: disabled
- GPU: disabled
- Architecture: x86_64
- Git commit tested: `2288520`
- Model SHA-256: `90defe5e1199ac4265916a362b47f6d0ecc24430c97fd047851445842da53a04`
- NumPy: 2.2.6
- ONNX: 1.22.0
- ONNX Runtime: 1.23.2
- OpenCV package: 5.0.0.93
- Active inference provider: `CPUExecutionProvider`

### Validation results

- Model contract tests: 2/2 passed
- Held-out images tested: 29
- Expected category matched local results: 29/29
- Retained region counts matched local results: 29/29
- False activation matched local results: Pitted surface on `patches_274.jpg`
- Representative overlays matched the local qualitative assessment.
- No preprocessing, BGR channel-order, resizing, normalization or post-processing differences were found.
- The model ran successfully across Apple M3 locally and x86_64 in Cloudera.

### Performance

- Average CPU inference: 11.58 ms
- Median CPU inference: 11.61 ms
- CPU inference range: 6.99–13.41 ms
- Model-loading time: 343.27 ms
- Peak process memory after model loading: 276.36 MiB
- Peak memory increase during model loading: 237.79 MiB

The Cloudera runtime was faster than the stable local readings, which were generally between 21 and 30 ms.

### Environment issues

- Cloudera pip configuration set `install.user=true`, which conflicts with virtual environments.
- Dependencies were installed successfully using the `--no-user` option.
- `/usr/bin/time` was unavailable, so memory was measured with Python's built-in `resource` module.
- Cloudera and Jupyter runtime files were added to `.gitignore`.

### Phase 3 decision

**Passed.** The model runs without a GPU, contract tests pass, predictions and retained region counts match the local results, overlays remain consistent, and CPU performance is sufficient for the demo.

## Current decision
**Technical result: passed.**
The model loads correctly, runs on CPU and satisfies its input/output contract.

**Quality result: passed for the demo, with limitations.**
The expected category activated on all 29 reviewed images. One cross-class false activation occurred. Localization is suitable for an approximate visual indication, but not for claiming precise defect boundaries.

**Final Step 1 decision: usable.**
The model passed both local and Cloudera CPU validation and can proceed to the next design phase. It should not yet be used for automatic production rejection decisions.
## Deployed endpoint validation — 2026-09-23

- Deployment: `steel-defect-onnx-api-v4`; Model ID: 10.
- Serving entry point: `src/serve_onnx.py`, function `predict`.
- Test image: `data/crazing_241.jpg`.
- Client input: `(1, 3, 128, 128)`, float32.
- HTTP status: 200.
- Response success: true.
- Output shape: `(1, 6, 128, 128)`.
- All output values finite: true.
- Existing postprocessing defaults: probability > 0.5;
  retain connected regions with more than 200 pixels before resizing.
- Detected class: Crazing.
- Retained regions: `[1, 0, 0, 0, 0, 0]`.
- Class activation and region counts match the validated baseline.
- Saved response: `outputs/crazing_241_v4_response.json`.
- Saved overlay: `outputs/crazing_241_v4_overlay.jpg`.
- Endpoint overlay visual review and numerical comparison with local
  raw outputs were not performed in this check.

### Resolved request mismatch

The client sent `request.inputs`, while the serving function read
`args["input"]`. The installed decorator passes the parsed dictionary
without renaming these keys and returns None for missing keys.
Changing the client to `request.input` resolved the scalar-shape error.
No deployment rebuild was needed for this client change.

### Decision

Passed endpoint inference and baseline class/region-count validation
for one image. This does not extend the earlier quality assessment
or establish endpoint accuracy across all six classes.


## Inspection function validation — 2026-09-24

Added `src/inspection.py` with `inspect_image(image_path)`.
It calls the deployed endpoint and reuses the existing preprocessing,
postprocessing and visualization functions. It returns a JSON-compatible
dictionary and saves an inspection JSON file and overlay under `outputs/`.

### Verified in Cloudera Workbench

| Image | Detected class | Retained regions | Approximate mask area |
|---|---|---:|---:|
| crazing_241.jpg | Crazing | 1 | 60.66% |
| patches_274.jpg | Patches | 1 | 13.14% |
| patches_274.jpg | Pitted surface | 1 | 1.51% |
| scratches_86.jpg | Scratches | 3 | 17.83% |

- Deployment: `steel-defect-onnx-api-v4`, Model ID 10.
- Class activations and region counts match the recorded baseline.
- The known extra Pitted surface activation on patches_274.jpg persists.
- Output shape and finite-value checks passed for all three calls.
- Settings: probability > 0.5; connected regions > 200 pixels at
  128 x 128 resolution, before resizing.
- Crazing endpoint round trip: 1642.94 ms; inspection before JSON save:
  1826.50 ms. These are single observations, not an inference benchmark.
- Patches and Scratches overlays were visually reviewed in chat.
  Scratches outlines follow three visible scratches; labels overlap slightly.
  Patches shows the main patch and the known extra activation.
- The new Crazing inspection overlay was not visually reviewed here.

### Limits and next step

Mask area is approximate image coverage, not a precise damaged-area
measurement. Region counts are mask components, not confirmed defect counts.
The underlying registry version is unverified; model_version remains null.
No numerical comparison of endpoint logits with local logits was performed.

A screenshot showed Qwen2.5-7B-Instruct running. Its API access, request
format and tool-calling support remain unverified. Next: obtain a redacted
API usage example, test access, then connect the inspection function.
Agent, guidance lookup and UI implementation have not started.
