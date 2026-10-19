# Phase 4 -- Reproducing the Cloudera AI Registry registration on another Workbench

Goal: attempt the exact same ONNX model registration that has failed with
`Failed to create model registry directory in storage: exit status 1` on a
different Cloudera AI Workbench, to help tell whether this is specific to one
Workbench/environment/AWS region or affects the setup more broadly.

## 1. Get the model file
This repository does not include `model/Unet.onnx` (its reuse licence is not
yet confirmed, so it is deliberately excluded via `.gitignore`). Obtain the
file through the approved internal channel -- do not use a public link or
broaden its distribution beyond this diagnostic. Place it at
`model/Unet.onnx` and verify it before doing anything else:

    sha256sum model/Unet.onnx
    # expected: 90defe5e1199ac4265916a362b47f6d0ecc24430c97fd047851445842da53a04

If the hash does not match, stop -- you do not have the validated model.

## 2. Enable the Cloudera runtime add-on
Registration depends on the `mlflow-cml-plugin` runtime add-on (confirmed
version 0.0.1 here), which is not a pip package. In your Workbench project
settings, enable the MLflow / Cloudera ML registry runtime add-on before
creating the environment below.

## 3. Create the registration environment

    python3 -m venv .venv-registry
    source .venv-registry/bin/activate
    pip install --upgrade pip
    pip install -r requirements-registry.txt
    pip check
    # expect: "No broken requirements found."

Do not upgrade `mlflow-skinny`, `protobuf`, or `typing-extensions` beyond the
pinned versions -- the plugin requires exactly these.

## 4. Confirm MLflow routing

    echo $MLFLOW_TRACKING_URI
    echo $MLFLOW_REGISTRY_URI
    # both should be: cml://localhost

## 5. Run the registration

    .venv-registry/bin/python scripts/register_onnx_model.py <your-workbench-name>

This uses the same input/output signature, tags, and `mlflow.onnx.log_model`
call used in every attempt so far (single-file packaging,
`save_as_external_data=False`,
`pip_requirements=["onnx==1.16.2","onnxruntime==1.23.2"]`,
`await_registration_for=300`). Do not edit the script -- if you need to
change something to get it running, that itself is a meaningful finding, so
note exactly what you changed.

## 6. Check the result in the Registry UI, not the terminal
MLflow prints "Successfully registered" / "Created version" regardless of
whether the Cloudera AI Registry import actually succeeded. Open the AI
Registry UI, find the new version under `steel-defect-unet`, and record:
- Status (Ready / Failed)
- If Failed, the full error text (expand/widen if it's truncated)
- Run ID, version number, created-at timestamp

## 7. Report back
Whatever the result, report:
- Your Workbench name, AWS region/account (if known), Workbench version
- The run ID and version number created
- The full status and error text from the Registry UI
- Confirmation that the model hash matched before you ran the registration

If it succeeds where this environment failed, that points toward an
environment- or region-specific cause. If it fails with the same "Failed to
create model registry directory in storage: exit status 1" error, that
points toward something shared between both setups rather than a purely
local/regional problem.
