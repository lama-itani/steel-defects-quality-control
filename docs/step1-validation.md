# Step 1 — ONNX Model Validation

## Current status
**2026-Sept-16**
The ONNX model works technically on the local CPU. Phase 2 prediction-quality validation is in progress. Crazing is complete; five defect categories remain.

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

## Current decision

**Technical result: passed.**
The model loads, runs on CPU and produces usable binary masks.

**Quality decision: pending.**
Test 3–5 images from each defect category before deciding whether the model is suitable for the demo.