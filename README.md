# Steel Defect Quality Control

Local validation pipeline for an existing ONNX model that detects six steel surface defect categories.

This repository currently covers technical model validation. It is not yet a production application or an agent-based system.

## Current status
- ONNX model loads successfully.
- CPU inference works on Apple Silicon.
- Input: `[1, 3, 128, 128]`, FP32
- Output: `[1, 6, 128, 128]`, FP32
- Preprocessing, inference, post-processing and visualization are implemented.
- Model contract tests pass.
- CPU inference time observed: 21.98–23.42 ms across 2 runs
- Prediction quality testing across all defect categories is pending.

## Setup
Python 3.10 is recommended.

```bash
python3.10 -m venv .venv310
source .venv310/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt