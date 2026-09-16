# Step 1 — ONNX Model Validation

## Current status
**2026-Sept-16**
The ONNX model works technically on the local CPU. Phase 2 prediction-quality validation is in progress. Crazing, Patches and Inclusion are complete; three defect categories remain.
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

## Current decision

**Technical result: passed.**
The model loads, runs on CPU and produces usable binary masks.

**Quality decision: pending.**
Test 3–5 images from each defect category before deciding whether the model is suitable for the demo.