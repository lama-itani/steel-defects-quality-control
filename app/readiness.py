import sys
from datetime import datetime, timezone
from pathlib import Path

import streamlit as st

root = Path.cwd().resolve()
if str(root) not in sys.path:
    sys.path.insert(0, str(root))

from src.qc_tools import SAMPLES, inspect_image
from src.qc_agent import run_agent

SAMPLE_LABELS = {"scratches_86.jpg": "Sample 01", "patches_274.jpg": "Sample 02"}
for _name in SAMPLES:
    SAMPLE_LABELS.setdefault(_name, f"Sample {len(SAMPLE_LABELS) + 1:02d}")
histories = st.session_state.setdefault("qc_histories", {})


def display_history(entries):
    for entry in entries:
        with st.chat_message("user"):
            st.write(entry["question"])
        with st.chat_message("assistant"):
            answer = entry["response"]
            st.caption("Draft for human review · " + entry["created_at"])
            if answer["status"] != "completed":
                st.warning("Agent response incomplete. Inspection evidence remains available.")
            st.markdown(answer["answer"])
            with st.expander("Agent tool evidence"):
                st.json(answer)

st.set_page_config(page_title="Steel Surface QC", layout="wide")
st.title("Steel Surface QC")
st.caption("Visual inspection · Evidence review · AI explanation")
st.warning("DRAFT — FOR HUMAN REVIEW. No automatic material decisions.")

with st.sidebar:
    st.header("Inspection")
    sample = st.selectbox(
        "Select a sample", list(SAMPLES),
        format_func=lambda value: SAMPLE_LABELS[value],
    )
    inspect_clicked = st.button("Run inspection", type="primary")
    st.caption("Inspection runs only when clicked.")
    st.divider()
    st.caption("Six-class detector. Masks and areas are approximate.")

# Prevent results from a different sample appearing beside this image.
if st.session_state.get("qc_sample") != sample:
    for key in ("qc_result", "qc_answer", "qc_error"):
        st.session_state.pop(key, None)
    st.session_state["qc_sample"] = sample

if inspect_clicked:
    for key in ("qc_result", "qc_answer", "qc_error"):
        st.session_state.pop(key, None)
    try:
        with st.spinner("Inspecting steel surface…"):
            st.session_state["qc_result"] = inspect_image(sample)
    except Exception:
        st.session_state["qc_error"] = (
            "Inspection failed. Please retry or check Application logs."
        )

if st.session_state.get("qc_error"):
    st.error(st.session_state["qc_error"])

result = st.session_state.get("qc_result")
original_col, overlay_col = st.columns(2)

with original_col:
    st.subheader("Original image")
    st.image(str(root / SAMPLES[sample]), caption=SAMPLE_LABELS[sample], width=400)

with overlay_col:
    st.subheader("Model overlay")
    if result:
        st.image(
            result["overlay_path"],
            caption="Approximate masks — not precise defect boundaries",
            width=400,
        )
    else:
        st.info("Run an inspection to view its overlay and findings.")

if result:
    st.subheader("Inspection findings")
    st.caption(
        f"Inspection ID: {result['inspection_id']} · "
        f"Sample: {SAMPLE_LABELS[sample]}"
    )

    if result["findings"]:
        st.dataframe(
            [
                {
                    "Class activation": item["class_name"],
                    "Mask components": item["retained_regions"],
                    "Approximate area (%)":
                        item["approximate_mask_area_percent"],
                }
                for item in result["findings"]
            ],
            hide_index=True,
            width="stretch",
        )
    else:
        st.info("No retained detections. This does not mean defect-free.")

    with st.expander("Limitations", expanded=True):
        st.write("• Masks and affected areas are approximate.")
        st.write("• Regions are mask components, not confirmed defects.")
        st.write("• No detections does not mean defect-free.")

    st.subheader("Ask the QC agent")
    st.caption("Questions and answers are kept for this session. Each question is answered independently.")
    history = histories.setdefault(result["inspection_id"], {
        "sample_label": SAMPLE_LABELS[sample], "entries": [],
    })
    with st.form("qc_question_form_" + result["inspection_id"]):
        question = st.text_input(
            "Question about this inspection",
            value="Summarize all findings and explain the limitations.",
        )
        ask = st.form_submit_button("Ask agent")

    if ask:
        if not question.strip():
            st.info("Enter a question first.")
        else:
            try:
                with st.spinner("Reviewing inspection evidence…"):
                    answer = run_agent(
                        f"Retrieve inspection {result['inspection_id']}. "
                            "Answer the user's question directly using the saved evidence. "
                            "Do not run a new inspection. "
                            "Adapt your response: summarize briefly for a summary request; "
                            "explain relevant findings for an explanation request; "
                            "write a report only when explicitly requested. "
                            "Never omit findings when summarizing the inspection. "
                            "Check guidance only when relevant; acknowledge if unavailable. "
                            "Include the inspection ID. All answers remain drafts for human review.\n"
                            f"Refer to this image as {SAMPLE_LABELS[sample]}, not its filename.\n"
                            f"User question: {question}"
                    )
            except Exception:
                answer = {
                    "status": "error",
                    "answer": "Agent unavailable. Inspection evidence remains available.",
                    "tool_results": [],
                    "report_status": "draft_for_human_review",
                }
            history["entries"].append({
                "question": question.strip(),
                "response": answer,
                "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            })

    display_history(history["entries"])

    with st.expander("Saved inspection evidence"):
        display_result = dict(result)
        display_result["image_id"] = SAMPLE_LABELS[sample]
        st.caption("Display uses a neutral sample label; saved evidence retains the original filename.")
        st.json(display_result)

current_id = result["inspection_id"] if result else None
earlier = {
    inspection_id: history
    for inspection_id, history in histories.items()
    if inspection_id != current_id and history["entries"]
}
if earlier:
    with st.expander("Earlier inspection conversations"):
        for inspection_id, history in earlier.items():
            st.caption(f"{history['sample_label']} · Inspection ID: {inspection_id}")
            display_history(history["entries"])

