import json
import re
import sys
from collections import Counter
from pathlib import Path

import cv2
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src import catalog, review_logic as rl, review_store as rs
from src.qc_agent import run_agent
from src.visualization import CLASS_COLORS, create_defect_overlay

MAPPING = json.loads((ROOT / "config/class_mapping.json").read_text())
CLASS_IDS = {name: int(i) for i, name in MAPPING.items()}
ID_RE = re.compile(r"[0-9a-f]{32}")
VERDICTS = ["agree", "disagree", "unsure"]
STATUS_LABEL = {
    "not_inspected": "Not inspected",
    "not_reviewed": "Not reviewed",
    "agree": "Agree",
    "disagree": "Disagree",
    "unsure": "Unsure",
}
FLAG_LABEL = {
    "extra_class": "Extra class detected",
    "expected_missing": "Expected class not detected",
    "no_detection": "Nothing detected",
}

st.set_page_config(page_title="Steel QC review", layout="wide")


@st.cache_data(ttl=60)
def load_data():
    latest = rs.latest_inspections()
    reviews = {}
    for result in latest.values():
        review = rs.latest_review(result["inspection_id"])
        if review:
            reviews[result["inspection_id"]] = review
    return latest, reviews


NAV_CSS = """
<style>
[class*="st-key-nav_"] button {
    background-color: #1f4e79; color: #fff; border: 1px solid #1f4e79;
}
[class*="st-key-nav_"] button:hover:not(:disabled) {
    background-color: #2a6aa5; border-color: #2a6aa5; color: #fff;
}
[class*="st-key-nav_"] button:disabled {
    background-color: #c5ced8; border-color: #c5ced8; color: #6b7785;
}
</style>
"""


def go(image=None):
    if image:
        st.query_params["image"] = image
    else:
        st.query_params.clear()


def overlay_file(iid):
    path = rs.STORE / iid / "overlay.jpg"
    return str(path) if path.is_file() else None


def filter_text(flt):
    parts = [flt["class"] or "All classes"]
    if flt["mismatch"]:
        parts.append("mismatch only")
    if flt["status"]:
        parts.append(STATUS_LABEL[flt["status"]])
    return ", ".join(parts)


def filter_ui(rows, flt):
    counts = Counter(r["expected_class"] for r in rows)
    labels = {f"All ({len(rows)})": None}
    for name in catalog.PREFIX_TO_CLASS.values():
        labels[f"{name} ({counts[name]})"] = name
    default = next(k for k, v in labels.items() if v == flt["class"])
    choice = st.pills(
        "Class", list(labels), selection_mode="single",
        default=default, label_visibility="collapsed",
    )
    flt["class"] = labels.get(choice)

    left, right = st.columns(2)
    flt["mismatch"] = left.checkbox("Mismatch only", value=flt["mismatch"])
    options = [None, *STATUS_LABEL]
    flt["status"] = right.selectbox(
        "Review status", options, index=options.index(flt["status"]),
        format_func=lambda s: "All" if s is None else STATUS_LABEL[s],
    )


def class_hex(name):
    blue, green, red = CLASS_COLORS[CLASS_IDS[name]]
    return f"#{red:02x}{green:02x}{blue:02x}"


def class_chip(name):
    blue, green, red = CLASS_COLORS[CLASS_IDS[name]]
    text = "#000" if 0.299 * red + 0.587 * green + 0.114 * blue > 150 else "#fff"
    return (
        f"<span style='background:{class_hex(name)};color:{text};"
        "padding:1px 8px;border-radius:10px;margin-right:4px;"
        f"font-size:0.8em;white-space:nowrap'>{name}</span>"
    )


def card(row):
    with st.container(border=True):
        iid = row["inspection_id"]
        if iid:
            path = overlay_file(iid)
            if path:
                st.image(path, width="stretch")
            else:
                st.caption("Overlay unavailable")
        else:
            st.info("Not inspected – run the batch Job")
        st.markdown(f"**{row['image_id']}**")
        if iid:
            regions = sum(f["retained_regions"] for f in row["findings"])
            if row["detected_classes"]:
                chips = "".join(class_chip(c) for c in row["detected_classes"])
                st.markdown(
                    f"{chips}<span style='font-size:0.8em'>· {regions} regions</span>",
                    unsafe_allow_html=True,
                )
            else:
                st.caption(f"Detected: None · {regions} regions")
            if row["flag"]:
                st.caption(f":orange[{FLAG_LABEL[row['flag']]}]")
        st.caption(STATUS_LABEL[row["status"]])
        st.button(
            "Open", key=f"open_{row['image_id']}",
            on_click=go, args=(row["image_id"],),
        )


def overview(rows, flt, deployment):
    st.title("Steel QC · Inspection review")
    st.caption(f"Deployment: {deployment} · Results are drafts for human review")
    if st.session_state.get("flash"):
        st.success(st.session_state.pop("flash"))

    s = rl.summary(rows)
    cols = st.columns(4)
    cols[0].metric("Images", s["total"])
    cols[1].metric("Expected class detected", s["expected_detected"])
    cols[2].metric("Images with a flag", s["flagged"])
    cols[3].metric("Reviewed", s["reviewed"])

    filter_ui(rows, flt)
    filtered = rl.filter_rows(
        rows, flt["class"], flt["mismatch"], flt["status"]
    )
    nxt = rl.next_unreviewed(filtered)
    if st.button("Start review: next unreviewed", type="primary"):
        if nxt:
            go(nxt)
            st.rerun()
        st.info("Nothing left to review in this filter.")

    st.caption(f"{len(filtered)} of {len(rows)} images")
    for start in range(0, len(filtered), 4):
        for col, row in zip(st.columns(4), filtered[start:start + 4]):
            with col:
                card(row)


GUIDANCE_RULES = (
    "Judge guidance for each class only by the status in that class's own "
    "lookup result. If the status is guidance unavailable, say only that no "
    "guidance is available for that class and do not mention drafts. If the "
    "status is draft_pending_review, call it unreviewed draft guidance and "
    "cite its sources."
)
EXAMPLE_QUESTIONS = [
    "What was detected in this image, and does it match the expected class?",
    "What limitations should I keep in mind for this result?",
]


def run_chat(iid, question):
    if not ID_RE.fullmatch(iid) or not question.strip():
        return
    task = (
        "Answer the user's question using the saved evidence. Look up "
        "guidance only if the question needs it."
    )
    prompt = (
        f"Retrieve inspection {iid}. Do not run a new inspection. {task} "
        f"{GUIDANCE_RULES} Include the inspection ID and label the answer "
        f"as a draft for human review.\nUser question: {question.strip()}"
    )
    try:
        with st.spinner("Reviewing inspection evidence…"):
            out = run_agent(prompt)
    except Exception as error:
        out = {
            "status": "error",
            "answer": f"Agent unavailable ({type(error).__name__}).",
            "tool_results": [],
        }
    st.session_state.setdefault("agent", {}).setdefault(iid, []).append({
        "question": question.strip(),
        "response": out,
    })


def detail(image, rows, filtered, flt):
    row = next(r for r in rows if r["image_id"] == image)
    iid = row["inspection_id"]
    nav = filtered if any(r["image_id"] == image for r in filtered) else rows
    prev_id, next_id = rl.neighbours(nav, image)
    position = [r["image_id"] for r in nav].index(image) + 1

    st.markdown(NAV_CSS, unsafe_allow_html=True)
    bar = st.columns([1, 3, 1, 1, 1.6])
    bar[0].button("Back to grid", key="nav_back", on_click=go)
    bar[1].markdown(
        f"Image {position} of {len(nav)} · Filter: {filter_text(flt)}"
    )
    bar[2].button("Previous", key="nav_prev", disabled=not prev_id, on_click=go, args=(prev_id,))
    bar[3].button("Next", key="nav_next", disabled=not next_id, on_click=go, args=(next_id,))
    unreviewed = rl.next_unreviewed(nav, image)
    bar[4].button(
        "Next unreviewed", key="nav_unreviewed", disabled=not unreviewed,
        on_click=go, args=(unreviewed,),
    )

    st.header(image)
    original = cv2.imread(str(catalog.sample_path(image)))
    if not iid:
        if original is not None:
            st.image(original, channels="BGR", width=400)
        st.info("Not inspected – run the batch Job")
        return

    result = load_data()[0][image]
    detected = row["detected_classes"]
    left, right = st.columns([3, 2])

    with left:
        image_box = st.container()
        overlay, channels = overlay_file(iid), "RGB"
        masks = None
        try:
            masks = rs.load_masks(iid)
        except Exception as error:
            st.caption(f"Masks unavailable ({type(error).__name__}).")
        if masks is not None and original is not None and detected:
            shown = [
                c for c in detected
                if st.checkbox(c, True, key=f"show_{iid}_{c}")
            ]
            kept = masks.copy()
            for c in detected:
                if c not in shown:
                    kept[CLASS_IDS[c]] = 0
            try:
                overlay, _ = create_defect_overlay(original, kept, MAPPING)
                channels = "BGR"
            except ValueError:
                st.caption("Overlay rebuild failed; showing saved overlay.")
        elif masks is None:
            st.caption("Mask toggles need a new inspection.")

        with image_box:
            a, b = st.columns(2)
            a.caption("Original")
            if original is not None:
                a.image(original, channels="BGR", width="stretch")
            b.caption("Overlay")
            if overlay is not None:
                b.image(overlay, channels=channels, width="stretch")

        st.subheader("QC agent")
        st.caption("Try an example question:")
        for n, example in enumerate(EXAMPLE_QUESTIONS):
            if st.button(example, key=f"example_{iid}_{n}"):
                run_chat(iid, example)
        with st.form(f"chat_{iid}", clear_on_submit=True):
            question = st.text_input("Question")
            ask = st.form_submit_button("Ask")
        if ask:
            if question.strip():
                run_chat(iid, question)
            else:
                st.info("Enter a question first.")
        for turn in reversed(st.session_state.get("agent", {}).get(iid, [])):
            out = turn["response"]
            with st.chat_message("user"):
                st.write(turn["question"])
            with st.chat_message("assistant"):
                st.warning("DRAFT — FOR HUMAN REVIEW")
                st.caption(f"Status: {out['status']}")
                st.markdown(out["answer"])
                with st.expander("Agent tool results"):
                    st.json(out.get("tool_results", []))

    with right:
        expected = row["expected_class"]
        st.markdown(
            f"**Expected:** {expected}  \n"
            f"**Detected:** {', '.join(detected) or 'None'}"
        )
        if row["flag"]:
            st.warning(FLAG_LABEL[row["flag"]])

        st.subheader("Findings")
        if row["findings"]:
            st.dataframe(
                [
                    {
                        "Class": f["class_name"],
                        "Retained regions": f["retained_regions"],
                        "Approx. area (%)": f["approximate_mask_area_percent"],
                    }
                    for f in row["findings"]
                ],
                hide_index=True, width="stretch",
            )
        else:
            st.info("No retained detections. This does not mean defect-free.")
        cfg = result.get("settings", {})
        st.caption(
            f"Threshold > {cfg.get('probability_threshold_exclusive')}, "
            f"min region > {cfg.get('min_region_pixels_exclusive')} px "
            f"at {cfg.get('region_filter_resolution')}"
        )

        st.subheader("Review")
        with st.form(f"review_{iid}"):
            verdict = st.radio(
                "Verdict", VERDICTS, index=None,
                format_func=str.capitalize, horizontal=True,
            )
            note = st.text_area("Note", max_chars=rs.MAX_NOTE)
            submitted = st.form_submit_button(
                "Save and go to next unreviewed", type="primary"
            )
        if submitted:
            if verdict is None:
                st.error("Choose a verdict.")
            elif verdict == "disagree" and not note.strip():
                st.error("A note is required for Disagree.")
            else:
                try:
                    rs.append_review(iid, verdict, note)
                except Exception as error:
                    st.error(f"Save failed ({type(error).__name__}).")
                else:
                    nxt = rl.next_unreviewed(nav, image)
                    st.cache_data.clear()
                    if not nxt:
                        st.session_state["flash"] = "Review saved. Nothing left to review."
                    go(nxt)
                    st.rerun()

        history = rs.review_history(iid)
        if history:
            st.caption("History")
            for h in history:
                st.markdown(
                    f"**{h['verdict'].capitalize()}** · "
                    f"{h.get('reviewed_at', '')[:19]}  \n{h.get('note', '')}"
                )

        with st.expander("Limitations"):
            for item in result.get("limitations", []):
                st.write(f"• {item}")
        with st.expander("Raw JSON"):
            st.json(result)


try:
    latest, reviews = load_data()
except Exception as error:
    st.error(f"Could not load inspections ({type(error).__name__}).")
    st.stop()

rows = rl.build_rows(latest, reviews)
flt = st.session_state.setdefault(
    "flt", {"class": None, "mismatch": False, "status": None}
)
deployment = next(
    (r.get("deployment_name") for r in latest.values()), "unknown"
)

image = st.query_params.get("image")
if image in catalog.SAMPLE_FILES:
    filtered = rl.filter_rows(rows, flt["class"], flt["mismatch"], flt["status"])
    detail(image, rows, filtered, flt)
else:
    overview(rows, flt, deployment)
