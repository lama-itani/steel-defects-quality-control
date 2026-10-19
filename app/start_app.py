import os
import subprocess
import sys
from pathlib import Path

try:
    root = Path(__file__).resolve().parents[1]
except NameError:  # AMP tasks run scripts like notebook cells
    root = Path.cwd()
if not (root / "app" / "review_app.py").is_file():
    raise RuntimeError(f"Review app not found under project directory: {root}")

subprocess.run(
    [
        sys.executable, "-m", "streamlit", "run",
        str(root / "app/review_app.py"),
        "--server.address=127.0.0.1",
        "--server.port=" + os.environ["CDSW_READONLY_PORT"],
        "--server.headless=true",
        "--browser.gatherUsageStats=false",
    ],
    cwd=root,
    check=True,
)
