from html import escape
from string import Template

import streamlit as st

NAVY = "#1f4e79"
NAVY_HOVER = "#2a6aa5"
TINT = "#e8f0f8"
TINT_HOVER = "#d6e4f2"
TINT_BORDER = "#bcd0e5"
INK = "#1d2433"
MUTED = "#5b6474"
PAGE = "#f4f6f9"
CARD = "#ffffff"
LINE = "#e1e5eb"
AMBER = "#b45309"
AMBER_BG = "#fdf3e7"
DISABLED_BG = "#c5ced8"
PLACEHOLDER_BG = "#eef1f5"

BAND_COLORS = ["#a9cbe9", "#4a86c5", "#1f4e79"]
VERDICT_COLORS = {
    "agree": "#1f4e79",
    "disagree": "#d9822b",
    "unsure": "#f2c14e",
    "not_reviewed": "#d5dbe3",
}
FONT = "Source Sans Pro, Source Sans 3, sans-serif"

BADGES = {
    "flag": (AMBER_BG, AMBER),
    "agree": (VERDICT_COLORS["agree"], "#ffffff"),
    "disagree": (VERDICT_COLORS["disagree"], INK),
    "unsure": (VERDICT_COLORS["unsure"], INK),
    "not_reviewed": (VERDICT_COLORS["not_reviewed"], INK),
    "not_inspected": (PLACEHOLDER_BG, MUTED),
}

_CSS = Template("""
<style>
[data-testid="stMainBlockContainer"], .block-container {
    max-width: 1280px; padding-top: 4.5rem;
}
[data-testid="stMainBlockContainer"] h1 {
    font-size: 2rem !important; font-weight: 700 !important;
    letter-spacing: -0.01em; color: $INK;
}
[data-testid="stMainBlockContainer"] h2,
[data-testid="stMainBlockContainer"] h3 {
    font-size: 1.25rem !important; font-weight: 600 !important;
    letter-spacing: -0.01em; color: $INK;
}

/* Secondary buttons */
[data-testid="stBaseButton-secondary"],
[data-testid="stBaseButton-secondaryFormSubmit"],
[data-testid="stBaseButton-pills"],
[data-testid="stDownloadButton"] button {
    background-color: $TINT !important;
    border: 1px solid $TINT_BORDER !important;
    color: $NAVY !important;
    font-weight: 600 !important;
    border-radius: 8px !important;
}
[data-testid="stBaseButton-secondary"] p,
[data-testid="stBaseButton-secondaryFormSubmit"] p,
[data-testid="stBaseButton-pills"] p,
[data-testid="stDownloadButton"] button p {
    color: $NAVY !important; font-weight: 600 !important;
}
[data-testid="stBaseButton-secondary"]:hover:not(:disabled),
[data-testid="stBaseButton-secondaryFormSubmit"]:hover:not(:disabled),
[data-testid="stBaseButton-pills"]:hover:not(:disabled),
[data-testid="stDownloadButton"] button:hover:not(:disabled) {
    background-color: $TINT_HOVER !important;
    border-color: $TINT_BORDER !important;
    color: $NAVY !important;
}
[data-testid="stBaseButton-secondary"]:focus-visible,
[data-testid="stBaseButton-secondaryFormSubmit"]:focus-visible,
[data-testid="stBaseButton-pills"]:focus-visible,
[data-testid="stDownloadButton"] button:focus-visible {
    box-shadow: 0 0 0 2px rgba(31, 78, 121, 0.4) !important; outline: none;
}

/* Primary buttons and selected pills */
[data-testid="stBaseButton-primary"],
[data-testid="stBaseButton-primaryFormSubmit"],
[data-testid="stBaseButton-pillsActive"] {
    background-color: $NAVY !important;
    border: 1px solid $NAVY !important;
    color: #ffffff !important;
    font-weight: 600 !important;
    border-radius: 8px !important;
}
[data-testid="stBaseButton-primary"] p,
[data-testid="stBaseButton-primaryFormSubmit"] p,
[data-testid="stBaseButton-pillsActive"] p {
    color: #ffffff !important; font-weight: 600 !important;
}
[data-testid="stBaseButton-primary"]:hover:not(:disabled),
[data-testid="stBaseButton-primaryFormSubmit"]:hover:not(:disabled),
[data-testid="stBaseButton-pillsActive"]:hover:not(:disabled) {
    background-color: $NAVY_HOVER !important;
    border-color: $NAVY_HOVER !important;
}
[data-testid="stBaseButton-primary"]:focus-visible,
[data-testid="stBaseButton-primaryFormSubmit"]:focus-visible,
[data-testid="stBaseButton-pillsActive"]:focus-visible {
    box-shadow: 0 0 0 2px rgba(31, 78, 121, 0.4) !important; outline: none;
}

/* Navigation buttons (keys start with nav_) */
[class*="st-key-nav_"] button {
    background-color: $NAVY !important;
    border: 1px solid $NAVY !important;
    color: #ffffff !important;
    font-weight: 600 !important;
    border-radius: 8px !important;
}
[class*="st-key-nav_"] button p {
    color: #ffffff !important; font-weight: 600 !important;
}
[class*="st-key-nav_"] button:hover:not(:disabled) {
    background-color: $NAVY_HOVER !important;
    border-color: $NAVY_HOVER !important;
}

/* Disabled buttons */
button:disabled[data-testid^="stBaseButton"] {
    background-color: $DISABLED_BG !important;
    border-color: $DISABLED_BG !important;
    color: $MUTED !important;
}
button:disabled[data-testid^="stBaseButton"] p {
    color: $MUTED !important;
}

/* Cards: containers created with a key starting with card */
[class*="st-key-card"] {
    background-color: $CARD;
    border: 1px solid $LINE;
    border-radius: 10px;
    box-shadow: 0 1px 2px rgba(16, 24, 40, 0.06);
    padding: 1rem;
}
[class*="st-key-card_ov_"]:hover {
    box-shadow: 0 4px 12px rgba(16, 24, 40, 0.10);
}

/* Metrics */
[data-testid="stMetricLabel"] p {
    font-size: 13px !important; color: $MUTED !important;
}
[data-testid="stMetricValue"] {
    font-size: 30px !important; font-weight: 700 !important; color: $INK;
}

/* Tables, images, expanders */
[data-testid="stDataFrame"] {
    border: 1px solid $LINE; border-radius: 8px; overflow: hidden;
}
[data-testid="stImage"] img { border-radius: 8px; }
[data-testid="stExpander"] details {
    background-color: $CARD; border: 1px solid $LINE; border-radius: 10px;
}

/* Page header */
.qc-eyebrow {
    font-size: 12px; font-weight: 600; color: $MUTED;
    letter-spacing: 0.08em; text-transform: uppercase;
}
.qc-divider {
    border: 0; border-top: 1px solid $LINE; margin: 0.5rem 0 1rem;
}
.qc-muted { color: $MUTED; }
.qc-placeholder {
    background-color: $PLACEHOLDER_BG; color: $MUTED;
    border: 1px dashed $LINE; border-radius: 8px;
    aspect-ratio: 1 / 1; display: flex; align-items: center;
    justify-content: center; text-align: center; padding: 0.75rem;
    font-size: 0.9rem; margin-bottom: 0.5rem;
}
[class*="st-key-hdr_actions"] { align-items: flex-end; }
</style>
""")


def inject_css():
    css = _CSS.substitute(
        NAVY=NAVY, NAVY_HOVER=NAVY_HOVER, TINT=TINT, TINT_HOVER=TINT_HOVER,
        TINT_BORDER=TINT_BORDER, INK=INK, MUTED=MUTED, CARD=CARD, LINE=LINE,
        DISABLED_BG=DISABLED_BG, PLACEHOLDER_BG=PLACEHOLDER_BG,
    )
    st.markdown(css, unsafe_allow_html=True)


def card(name):
    return st.container(key=f"card_{name}")


def badge(text, kind):
    background, color = BADGES[kind]
    return (
        f"<span style='background:{background};color:{color};"
        "border-radius:999px;font-size:12px;font-weight:600;"
        "padding:2px 10px;white-space:nowrap;display:inline-block'>"
        f"{escape(str(text))}</span>"
    )


def page_header(title, subtitle, actions=None):
    left, right = st.columns([4, 1])
    with left:
        st.markdown("<div class='qc-eyebrow'>Steel QC</div>", unsafe_allow_html=True)
        st.title(title)
        st.caption(subtitle)
    if actions:
        with right:
            with st.container(key="hdr_actions"):
                for action in actions:
                    action()
    st.markdown("<hr class='qc-divider'>", unsafe_allow_html=True)


def metric_row(items):
    for col, (label, value) in zip(st.columns(len(items)), items):
        col.metric(label, value, border=True)
