# Validation data
## Source
The test images come from the `Validation_Images` folder in:
https://github.com/siddhartamukherjee/NEU-DET-Steel-Surface-Defect-Detection

The underlying dataset is NEU-DET.

## Current local images
- `crazing_241.jpg`
  - Expected category: Crazing
  - Used for initial pipeline validation

More images will be added for quality testing across all six categories.

## Storage and usage
- Images are stored locally under `data/`.
- Image files are excluded from Git.
- Dataset reuse and redistribution rights have not yet been confirmed.
- Do not commit or redistribute the images until the licence status is clear.

## Current validation scope
Only one image has been tested with the new ONNX pipeline. No aggregate Dice or IoU result has been calculated.