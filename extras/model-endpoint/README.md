# Optional: CML Model endpoint and registry

These files serve `model/Unet.onnx` as a CML Model endpoint and register it in the Model Registry.
They are optional and are NOT used by the AMP, which runs the ONNX model inside the app.
Paths inside the scripts assume the repo layout; run them from the repo root.
`cdsw-build.sh` holds the model SHA-256 check.
