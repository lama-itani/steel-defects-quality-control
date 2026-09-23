import json
import os
from pathlib import Path

import cmlapi
import numpy as np
import requests

from src.preprocessing import preprocess_image


MODEL_NAME = "steel-defect-onnx-api-v4"
URL = "https://modelservice.ml-a60a2d26-d1f.applied.jmgjgh.a0.cloudera.site/model"
IMAGE = "data/crazing_241.jpg"
OUTPUT = Path("outputs/crazing_241_v4_response.json")


# Find the exact deployment and retrieve its access key internally.
models = cmlapi.default_client().list_models(
    project_id=os.environ["CDSW_PROJECT_ID"]
).models
matches = [model for model in models if model.name == MODEL_NAME]

if len(matches) != 1:
    raise RuntimeError(f"Expected one {MODEL_NAME} deployment; found {len(matches)}")

access_key = matches[0].access_key
api_key = os.environ["CDSW_APIV2_KEY"]

tensor, _ = preprocess_image(IMAGE)
print("Input:", tensor.shape, tensor.dtype)

response = requests.post(
    URL,
    json={
        "accessKey": access_key,
        "request": {"input": tensor.tolist()},
    },
    headers={"Authorization": f"Bearer {api_key}"},
    timeout=120,
)
print("HTTP status:", response.status_code)

if not response.ok:
    # Remove either key if the server includes it in an error message.
    error = response.text.replace(access_key, "[redacted]")
    error = error.replace(api_key, "[redacted]")
    print("Error:", error[:800])
    raise SystemExit(1)

body = response.json()
OUTPUT.parent.mkdir(parents=True, exist_ok=True)
OUTPUT.write_text(json.dumps(body), encoding="utf-8")

print("Saved:", OUTPUT)
print("Response keys:", list(body) if isinstance(body, dict) else type(body).__name__)

payload = body.get("response", body) if isinstance(body, dict) else body
if isinstance(payload, dict):
    print("Payload keys:", list(payload))
    for name in ("output", "outputs", "prediction", "predictions"):
        if name in payload:
            array = np.asarray(payload[name])
            print("Output shape:", array.shape)
            print("All values finite:", bool(np.isfinite(array).all()))
            break
