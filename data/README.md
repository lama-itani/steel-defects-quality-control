# Sample data

## Source
The 29 sample images are synthetic. `scripts/generate_synthetic_samples.py` generates them procedurally (seed 2026) with no third-party images as input. They are stored in Git; nothing is downloaded at install time.

To reproduce them (development only, needs `scipy`): `python scripts/generate_synthetic_samples.py data`. The AMP does not run the generator; different numpy or OpenCV versions could change the pixels and break the baseline.

## Images
200×200 grayscale JPEG. The file name prefix is the expected defect class.

- Crazing: `crazing_1.jpg`, `crazing_2.jpg`, `crazing_3.jpg`, `crazing_4.jpg`, `crazing_5.jpg`
- Patches: `patches_1.jpg`, `patches_2.jpg`, `patches_3.jpg`, `patches_4.jpg`, `patches_5.jpg`
- Inclusion: `inclusion_1.jpg`, `inclusion_2.jpg`, `inclusion_3.jpg`, `inclusion_4.jpg`
- Pitted surface: `pitted_surface_1.jpg`, `pitted_surface_2.jpg`, `pitted_surface_3.jpg`, `pitted_surface_4.jpg`, `pitted_surface_5.jpg`
- Rolled-in scale: `rolled-in_scale_1.jpg`, `rolled-in_scale_2.jpg`, `rolled-in_scale_3.jpg`, `rolled-in_scale_4.jpg`, `rolled-in_scale_5.jpg`
- Scratches: `scratches_1.jpg`, `scratches_2.jpg`, `scratches_3.jpg`, `scratches_4.jpg`, `scratches_5.jpg`

`labels/<name>.txt` holds YOLO boxes per image (class order as in `config/class_mapping.json`). The app does not use them.

## Notes
- The generator was tuned against the shipped model, so results on these images do not measure accuracy on real steel.
- The crazing images look more stylised than real steel.
