import hashlib
import os
import shutil
import subprocess
import sys
from pathlib import Path

try:
    ROOT = Path(__file__).resolve().parents[1]
except NameError:  # AMP tasks run scripts like notebook cells
    ROOT = Path.cwd()
MODEL = ROOT / "model" / "Unet.onnx"
MODEL_SHA256 = (
    "90defe5e1199ac4265916a362b47f6d0ecc24430c97fd047851445842da53a04"
)


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for block in iter(lambda: file.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def main():
    free_gb = shutil.disk_usage(ROOT).free / 1e9
    print(f"CPU cores: {os.cpu_count()}, free disk: {free_gb:.1f} GB")

    if not MODEL.is_file():
        sys.exit(f"Model not found: {MODEL}")
    if sha256(MODEL) != MODEL_SHA256:
        sys.exit("model/Unet.onnx SHA-256 does not match the expected value")
    print("Model SHA-256 verified")

    subprocess.run(
        [sys.executable, "-m", "pip", "install", "-r",
         str(ROOT / "requirements.txt")],
        check=True,
    )

    (ROOT / "data").mkdir(exist_ok=True)
    (ROOT / "outputs" / "inspections").mkdir(parents=True, exist_ok=True)
    print("Install complete")


if __name__ == "__main__":
    main()
