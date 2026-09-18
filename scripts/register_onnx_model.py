import sys
import time
import mlflow
import mlflow.onnx
import onnx
import numpy as np
from mlflow.types.schema import Schema, TensorSpec
from mlflow.models.signature import ModelSignature

EXPERIMENT_NAME = "steel-defect-quality-control"
REGISTERED_MODEL_NAME = "steel-defect-unet"
MODEL_PATH = "model/Unet.onnx"
MODEL_SHA256 = "90defe5e1199ac4265916a362b47f6d0ecc24430c97fd047851445842da53a04"


def main():
    # Optional CLI arg lets you label the run (e.g. a workbench/host name);
    # defaults to a timestamp so it never collides on repeat runs.
    run_label = sys.argv[1] if len(sys.argv) > 1 else time.strftime("%Y-%m-%d-%H%M%S")
    run_name = f"single-file-retry-{run_label}"

    mlflow.set_experiment(EXPERIMENT_NAME)

    model = onnx.load(MODEL_PATH)

    input_schema = Schema([TensorSpec(np.dtype(np.float32), (1, 3, 128, 128), "input")])
    output_schema = Schema([TensorSpec(np.dtype(np.float32), (1, 6, 128, 128), "output")])
    signature = ModelSignature(inputs=input_schema, outputs=output_schema)

    with mlflow.start_run(run_name=run_name) as run:
        mlflow.set_tag("model_format", "ONNX")
        mlflow.set_tag("model_sha256", MODEL_SHA256)
        mlflow.set_tag("onnx_opset", "11")
        mlflow.set_tag("runtime_target", "CPU")
        mlflow.set_tag("onnx_packaging", "single-file")

        mlflow.onnx.log_model(
            onnx_model=model,
            artifact_path="model",
            registered_model_name=REGISTERED_MODEL_NAME,
            signature=signature,
            pip_requirements=["onnx==1.16.2", "onnxruntime==1.23.2"],
            save_as_external_data=False,
            await_registration_for=300,
        )

        print("RUN_ID:", run.info.run_id)
        print("RUN_NAME:", run.info.run_name)
        print("EXPERIMENT_ID:", run.info.experiment_id)


if __name__ == "__main__":
    main()
