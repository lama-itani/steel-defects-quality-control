# Deploy

The AMP runs three tasks in order (see `.project-metadata.yaml`).

| # | Task | Script | What it does |
|---|---|---|---|
| 1 | Install dependencies | `deploy/install.py` | Prints CPU and disk, verifies the SHA-256 of `model/Unet.onnx`, installs `requirements.txt`, creates `data/` and `outputs/inspections/` |
| 2 | Run baseline inspections | `scripts/run_batch_inspections.py` | Inspects the 29 images and compares retained regions per class with the validated baseline |
| 3 | Steel Surface QC | `app/start_app.py` | Starts the Streamlit review application (subdomain `steel-qc`) |

## Environment variables

| Name | Required | Default | Description |
|---|---|---|---|
| `QC_LLM_BASE_URL` | no | – | Cloudera AI Inference OpenAI-compatible base URL, ending in `/openai/v1` |
| `QC_LLM_MODEL` | no | – | Model name served by the endpoint |
| `QC_SHOW_DRAFT_GUIDANCE` | no | `0` | `1` shows unreviewed draft defect guidance in agent answers |

The agent reads its access token from `/tmp/jwt`. Without `QC_LLM_BASE_URL` or that file, the agent answers "LLM not configured" and the rest of the app works.

## Rerunning

Every script is safe to rerun. In a session, run `python deploy/install.py` or `python scripts/run_batch_inspections.py` (add `--only-missing` to skip images already inspected). To change an environment variable, edit it in the project settings and restart the application.
