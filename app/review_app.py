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

from src import catalog, qc_tools, review_logic as rl, review_store as rs
from src.qc_agent import run_agent
from src.visualization import create_defect_overlay

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
            detected = ", ".join(row["detected_classes"]) or "None"
            regions = sum(f["retained_regions"] for f in row["findings"])
            st.caption(f"Detected: {detected} · {regions} regions")
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


def run_explain(iid):
    if not ID_RE.fullmatch(iid):
        return
    prompt = (
        f"Retrieve inspection {iid}. Look up guidance for every returned "
        "defect class, then summarize all findings and limitations. Report "
        "the guidance status for each class. Label draft_pending_review "
        "guidance as unreviewed draft guidance and cite its sources. State "
        "which classes have no guidance available. Include the inspection "
        "ID and label the report as a draft for human review."
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
    st.session_state.setdefault("agent", {})[iid] = out


GUIDANCE_BADGE = {
    "approved": ":green[Approved]",
    "draft_pending_review": ":orange[Draft – pending review]",
    "guidance unavailable": ":gray[Guidance unavailable]",
}


def guidance_panel(detected):
    st.subheader("Handling guidance")
    document = (qc_tools.GUIDANCE or {}).get("document")
    if document is None:
        st.warning("Guidance file unavailable. No guidance can be shown.")
    else:
        doc_status = document.get("status")
        st.caption(
            f"Document version {document.get('version')} · "
            f"approval state: {doc_status}"
        )
        if doc_status != "approved":
            st.warning("Draft guidance – not approved for use")
    if not detected:
        st.caption("No detected classes.")
        return

    for name in detected:
        try:
            item = qc_tools.lookup_defect_guidance(name)
        except Exception as error:
            item = None
            failure = type(error).__name__
        status = item["status"] if item else "guidance unavailable"
        with st.expander(f"{name} · {status}"):
            st.markdown(GUIDANCE_BADGE.get(status, status))
            if item is None:
                st.caption(f"Guidance lookup failed ({failure}).")
                continue
            body = item["guidance"]
            if body is None:
                st.write("No reviewed guidance for this class.")
                continue
            if status != "approved":
                st.warning("Unreviewed draft guidance – not approved for use")
            st.markdown("**Definition**")
            st.write(body["definition"] or "None recorded")
            st.markdown("**Typical causes**")
            for cause in body["typical_causes"] or ["None recorded"]:
                st.write(f"• {cause}")
            st.markdown("**Common handling steps**")
            for step in body["common_handling"]:
                st.write(step)
            st.markdown("**Class-specific handling**")
            for step in body["class_specific_handling"] or ["None recorded"]:
                st.write(f"• {step}")
            st.markdown("**Sources**")
            for src in item["source"]:
                section = f", section {src['section']}" if src["section"] else ""
                st.markdown(
                    f"• [{src['citation']}]({src['url']}){section}  \n"
                    f"  _Access: {src['access']}_"
                )
            st.caption(f"Document version {item['version']}")


def detail(image, rows, filtered, flt):
    row = next(r for r in rows if r["image_id"] == image)
    iid = row["inspection_id"]
    nav = filtered if any(r["image_id"] == image for r in filtered) else rows
    prev_id, next_id = rl.neighbours(nav, image)
    position = [r["image_id"] for r in nav].index(image) + 1

    bar = st.columns([1, 3, 1, 1, 1.6])
    bar[0].button("Back to grid", on_click=go)
    bar[1].markdown(
        f"Image {position} of {len(nav)} · Filter: {filter_text(flt)}"
    )
    bar[2].button("Previous", disabled=not prev_id, on_click=go, args=(prev_id,))
    bar[3].button("Next", disabled=not next_id, on_click=go, args=(next_id,))
    unreviewed = rl.next_unreviewed(nav, image)
    bar[4].button(
        "Next unreviewed", disabled=not unreviewed,
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
        if st.button("Explain this inspection"):
            run_explain(iid)
        out = st.session_state.get("agent", {}).get(iid)
        if out:
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

        guidance_panel(detected)

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
