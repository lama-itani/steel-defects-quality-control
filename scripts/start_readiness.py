import os
import subprocess
import sys
import shutil
import socket
from pathlib import Path

root = Path.cwd().resolve()
if not (root / "app" / "readiness.py").is_file():
    raise RuntimeError(f"Readiness script not found under project directory: {root}")

for name in ("CDSW_APP_PORT", "CDSW_READONLY_PORT"):
    print(f"{name}={os.getenv(name)}", flush=True)

ss = shutil.which("ss")
if ss:
    diagnostic = subprocess.run(
        [ss, "-ltnp"], capture_output=True, text=True
    )
    print(diagnostic.stdout, flush=True)
    print(diagnostic.stderr, flush=True)
else:
    print("Listener diagnostic: ss is unavailable", flush=True)

for address in ("127.0.0.1", "0.0.0.0"):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
        try:
            probe.bind((address, int(os.environ["CDSW_APP_PORT"])))
            print(f"{address}:8100 — bind succeeded", flush=True)
        except OSError as error:
            print(f"{address}:8100 — {error}", flush=True)

subprocess.run(
    [
        sys.executable, "-m", "streamlit", "run",
        str(root / "app/readiness.py"),
        "--server.address=127.0.0.1",
        "--server.port=" + os.environ["CDSW_READONLY_PORT"],
        "--server.headless=true",
        "--browser.gatherUsageStats=false",
    ],
    cwd=root,
    check=True,
)
