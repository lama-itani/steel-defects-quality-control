import sys
from pathlib import Path

import requests

try:
    ROOT = Path(__file__).resolve().parents[1]
except NameError:  # AMP tasks run scripts like notebook cells
    ROOT = Path.cwd()
sys.path.insert(0, str(ROOT))

from src.catalog import SAMPLE_FILES  # noqa: E402

BASE_URL = (
    "https://raw.githubusercontent.com/siddhartamukherjee/"
    "NEU-DET-Steel-Surface-Defect-Detection/master/Validation_Images"
)
DATA_DIR = ROOT / "data"
JPEG_MAGIC = b"\xff\xd8\xff"


def main():
    DATA_DIR.mkdir(exist_ok=True)
    todo = [n for n in SAMPLE_FILES if not (DATA_DIR / n).is_file()]
    print(f"{len(SAMPLE_FILES) - len(todo)} present, {len(todo)} to download")

    failed = []
    for name in todo:
        try:
            response = requests.get(f"{BASE_URL}/{name}", timeout=30)
            response.raise_for_status()
            if not response.content.startswith(JPEG_MAGIC):
                raise ValueError("not a JPEG")
        except requests.ConnectionError:
            print(
                "No internet access. Upload the 29 images listed in "
                "data/README.md into data/ and rerun this task."
            )
            sys.exit(1)
        except Exception as error:
            failed.append(name)
            print(f"{name}: FAILED ({type(error).__name__})")
            continue

        temporary = DATA_DIR / (name + ".part")
        temporary.write_bytes(response.content)
        temporary.replace(DATA_DIR / name)
        print(f"{name}: downloaded")

    if failed:
        print("Missing files: " + ", ".join(failed))
        sys.exit(1)
    print(f"All {len(SAMPLE_FILES)} sample images are in data/")


if __name__ == "__main__":
    main()
