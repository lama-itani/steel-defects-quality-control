import os
import sys
from pathlib import Path
from importlib.metadata import version, PackageNotFoundError
import streamlit as st

st.title("Steel QC — readiness")
st.success("Workbench Application started")

st.write("Python:", sys.version.split()[0])
for package in ("streamlit", "openai", "cmlapi", "numpy", "requests"):
    try:
        st.write(f"{package}: {version(package)}")
    except PackageNotFoundError:
        st.error(f"{package}: missing package metadata")

st.json({
    "CDSW_PROJECT_ID_present": bool(os.getenv("CDSW_PROJECT_ID")),
    "CDSW_APIV2_KEY_present": bool(os.getenv("CDSW_APIV2_KEY")),
    "jwt_file_readable": os.access("/tmp/jwt", os.R_OK),
    "inspection_module_present": Path("src/inspection.py").is_file(),
    "sample_present": Path("data/scratches_86.jpg").is_file(),
})
st.caption("Credential presence only; endpoint access is not yet tested here.")

# Make the existing project modules importable
root = Path.cwd().resolve()
if str(root) not in sys.path:
    sys.path.insert(0, str(root))

st.subheader("Inspection endpoint test")

if st.button("Run Scratches inspection"):
    st.session_state.pop("inspection_probe", None)
    st.session_state.pop("inspection_probe_error", None)

    try:
        from src.inspection import inspect_image

        with st.spinner("Calling the existing inspection endpoint…"):
            result = inspect_image("data/scratches_86.jpg")

        st.session_state["inspection_probe"] = result
    except Exception as exc:
        # Do not display raw exceptions, which may contain request details.
        st.session_state["inspection_probe_error"] = type(exc).__name__

if "inspection_probe_error" in st.session_state:
    st.error(
        "Inspection failed: "
        + st.session_state["inspection_probe_error"]
        + ". Request details hidden."
    )

if "inspection_probe" in st.session_state:
    result = st.session_state["inspection_probe"]
    st.success("Inspection endpoint returned a result")
    st.json({
        "detected_classes": result.get("detected_classes"),
        "findings": result.get("findings"),
        "timing_ms": result.get("timing_ms"),
        "limitations": result.get("limitations"),
    })
    if result.get("overlay_path"):
        st.image(result["overlay_path"], caption="Approximate defect mask")

# Use verified Qwen configuration
st.subheader("LLM tool-calling test")

if st.button("Run LLM probe"):
    st.session_state.pop("llm_probe", None)
    stage = "authentication"

    try:
        import json
        from openai import OpenAI

        with open("/tmp/jwt") as jwt_file:
            token = json.load(jwt_file)["access_token"]

        model_id = "Qwen/Qwen2.5-7B-Instruct"
        tools = [{
            "type": "function",
            "function": {
                "name": "readiness_probe",
                "description": "Return the readiness marker.",
                "parameters": {
                    "type": "object",
                    "properties": {},
                    "required": [],
                    "additionalProperties": False,
                },
            },
        }]
        messages = [{
            "role": "user",
            "content": (
                "Call readiness_probe with no arguments. "
                "Then reply with only the marker returned by the tool."
            ),
        }]

        with st.spinner("Testing the LLM tool round trip…"):
            with OpenAI(
                base_url=(
                    "https://applied-ai.applied.jmgjgh.a0.cloudera.site"
                    "/namespaces/serving-default/endpoints"
                    "/qwen2-5-7b-instruct/openai/v1"
                ),
                api_key=token,
                timeout=30.0,
                max_retries=0,
            ) as client:
                stage = "tool request"
                first = client.chat.completions.create(
                    model=model_id,
                    messages=messages,
                    tools=tools,
                    tool_choice="auto",
                    temperature=0,
                    max_tokens=256,
                    stream=False,
                )
                message = first.choices[0].message
                calls = message.tool_calls or []

                stage = "tool validation"
                if len(calls) != 1:
                    raise ValueError("Expected exactly one tool call")

                call = calls[0]
                if (
                    call.type != "function"
                    or call.function.name != "readiness_probe"
                    or json.loads(call.function.arguments) != {}
                ):
                    raise ValueError("Unexpected tool or arguments")

                # Execute only this registered, harmless function.
                def readiness_probe():
                    return {"marker": "steel-qc-ready-731"}

                tool_result = readiness_probe()
                messages.append(
                    message.model_dump(exclude_none=True)
                )
                messages.append({
                    "role": "tool",
                    "tool_call_id": call.id,
                    "content": json.dumps(tool_result),
                })

                stage = "tool response consumption"
                final = client.chat.completions.create(
                    model=model_id,
                    messages=messages,
                    temperature=0,
                    max_tokens=256,
                    stream=False,
                )
                reply = final.choices[0].message
                passed = (
                    not reply.tool_calls
                    and (reply.content or "").strip()
                    == tool_result["marker"]
                )

        st.session_state["llm_probe"] = {
            "passed": passed,
            "tool_name_and_arguments_valid": True,
            "marker_exact_match": passed,
        }

    except Exception as exc:
        st.session_state["llm_probe"] = {
            "passed": False,
            "failed_stage": stage,
            "error_type": type(exc).__name__,
        }

if "llm_probe" in st.session_state:
    st.json(st.session_state["llm_probe"])

st.subheader("Full QC agent test")
st.caption("Runs a new Patches inspection only when clicked.")

if st.button("Run Patches agent test"):
    st.session_state.pop("agent_probe", None)
    st.session_state.pop("agent_probe_error", None)

    try:
        from src.qc_agent import run_agent

        with st.spinner("Running the QC agent…"):
            st.session_state["agent_probe"] = run_agent(
                "Inspect patches_274.jpg. Look up guidance for every "
                "returned defect class, then summarize all findings and "
                "limitations. State when guidance is unavailable. "
                "Include the inspection ID and label the report as "
                "a draft for human review."
            )
    except Exception as exc:
        st.session_state["agent_probe_error"] = type(exc).__name__

if "agent_probe_error" in st.session_state:
    st.error(
        "Agent test failed: "
        + st.session_state["agent_probe_error"]
        + ". Request details hidden."
    )

if "agent_probe" in st.session_state:
    agent_result = st.session_state["agent_probe"]

    st.warning("DRAFT — FOR HUMAN REVIEW")
    st.write("Agent status:", agent_result["status"])
    st.markdown(agent_result["answer"])

    # Keep tool evidence visible even if the LLM subsequently fails.
    st.json(agent_result)