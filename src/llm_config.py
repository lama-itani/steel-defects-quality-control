import json
import os
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "outputs" / "llm_config.json"


def _clean(value) -> str:
    return value.strip() if isinstance(value, str) else ""


def load() -> tuple[str, str]:
    """Return (base_url, model): saved values first, then environment."""
    saved = {}
    try:
        data = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            saved = data
    except (OSError, ValueError):
        pass

    base_url = _clean(saved.get("base_url")) or _clean(
        os.getenv("QC_LLM_BASE_URL")
    )
    model = _clean(saved.get("model")) or _clean(os.getenv("QC_LLM_MODEL"))
    return base_url, model


def save(base_url: str, model: str) -> None:
    base_url = _clean(base_url)
    model = _clean(model)
    if not base_url or not model:
        raise ValueError("Both the base URL and the model name are required")
    if not base_url.startswith(("http://", "https://")):
        raise ValueError("The base URL must start with http:// or https://")

    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        "w",
        encoding="utf-8",
        dir=CONFIG_PATH.parent,
        suffix=".tmp",
        delete=False,
    ) as handle:
        json.dump({"base_url": base_url, "model": model}, handle)
        temp_path = Path(handle.name)
    temp_path.replace(CONFIG_PATH)
