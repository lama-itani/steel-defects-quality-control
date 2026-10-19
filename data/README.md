# Sample data

## Source
The 29 sample images come from the `Validation_Images` folder in:
https://github.com/siddhartamukherjee/NEU-DET-Steel-Surface-Defect-Detection

The underlying dataset is NEU-DET (Northeastern University surface defect database).

`scripts/download_samples.py` downloads them into `data/` at install time (AMP task 2). The script skips files already present. If the machine has no internet access, upload the 29 images below into `data/` and rerun it.

## Required images
- Crazing: `crazing_151.jpg`, `crazing_153.jpg`, `crazing_166.jpg`, `crazing_240.jpg`, `crazing_241.jpg`
- Patches: `patches_28.jpg`, `patches_63.jpg`, `patches_128.jpg`, `patches_151.jpg`, `patches_274.jpg`
- Inclusion: `inclusion_161.jpg`, `inclusion_169.jpg`, `inclusion_195.jpg`, `inclusion_263.jpg`
- Pitted surface: `pitted_surface_18.jpg`, `pitted_surface_64.jpg`, `pitted_surface_110.jpg`, `pitted_surface_125.jpg`, `pitted_surface_175.jpg`
- Rolled-in scale: `rolled-in_scale_14.jpg`, `rolled-in_scale_80.jpg`, `rolled-in_scale_138.jpg`, `rolled-in_scale_176.jpg`, `rolled-in_scale_216.jpg`
- Scratches: `scratches_86.jpg`, `scratches_195.jpg`, `scratches_264.jpg`, `scratches_286.jpg`, `scratches_300.jpg`

The file name prefix is the expected defect class.

## Storage and licence
- Images are excluded from Git (`data/*.jpg`).
- Licence: # TODO — the source repository declares no licence and no usage terms. Dataset reuse and redistribution rights are not confirmed; do not commit or redistribute the images.
