import streamlit as st
import streamlit.components.v1 as _components_v1


class _ComponentsCompat:
    """components.html is deprecated in recent Streamlit in favour of st.iframe.
    Use st.iframe when available (same srcdoc/JS behaviour), else fall back."""

    @staticmethod
    def html(html, width=None, height=None, scrolling=False, **kw):
        import streamlit as _st
        if hasattr(_st, "iframe"):
            try:
                _w = width if isinstance(width, int) and width > 0 else "stretch"
                _h = height if isinstance(height, int) else "content"
                return _st.iframe(html, width=_w, height=_h)
            except Exception:
                pass
        return _components_v1.html(html, width=width, height=height, scrolling=scrolling, **kw)

    def __getattr__(self, name):
        return getattr(_components_v1, name)


components = _ComponentsCompat()
import json
import re
import os
import hashlib
import urllib.parse
import html as _html
from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime
from openai import OpenAI

# ═══════════════════════════════════════════════════
# PAGE CONFIG
# ═══════════════════════════════════════════════════
st.set_page_config(
    page_title="SanghaStatus",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ═══════════════════════════════════════════════════
# MULTI-TEAM SELECTION — must resolve BEFORE any per-team file (roster,
# history DB, presets, glossary) is touched below, so every persistence
# constant that follows can be suffixed with the active team's slug.
# Existing single-team users keep the original unsuffixed filenames as
# long as they stay on the "default" team, so nothing breaks for them.
# ═══════════════════════════════════════════════════
LAST_TEAM_FILE = ".sanghastatus_last_team.json"


def _slugify_team(name: str) -> str:
    slug = re.sub(r'[^a-z0-9]+', '-', (name or "").strip().lower()).strip('-')
    return slug or "default"


def _load_last_team() -> str:
    try:
        if os.path.exists(LAST_TEAM_FILE):
            with open(LAST_TEAM_FILE, "r") as f:
                return json.load(f).get("team_name", "default")
    except Exception:
        pass
    return "default"


def _save_last_team(name: str) -> None:
    try:
        with open(LAST_TEAM_FILE, "w") as f:
            json.dump({"team_name": name}, f)
    except Exception:
        pass


if "team_name" not in st.session_state:
    st.session_state.team_name = _load_last_team()

# ═══════════════════════════════════════════════════
# DESIGN SYSTEM — Apple/Samsung-style: calm surfaces, one accent, hairline cards.
# Dark mode: pure-CSS manual toggle (#dmchk + body:has) PLUS a
# prefers-color-scheme auto default that never fights the manual toggle
# (see the JS theme sync further down). Streamlit DOM hooks used are
# data-testid / baseweb attributes only; every selector degrades to the
# stock widget if it stops matching.
# SKIPPED (by design): a full custom React/Next.js front-end rewrite, and
# scroll-pinned "storytelling" sections — Streamlit's layout model makes
# both fragile.
# ═══════════════════════════════════════════════════
CSS = """
<style>

:root {
    --font:-apple-system,BlinkMacSystemFont,"SF Pro Display","SF Pro Text",Inter,"Segoe UI",Roboto,"Helvetica Neue",Arial,sans-serif;
    --mono:ui-monospace,"SF Mono",SFMono-Regular,Menlo,Consolas,monospace;
    /* 5-step type scale */
    --fs-1:0.8125rem; --fs-2:1rem; --fs-3:1.375rem; --fs-4:2.25rem; --fs-5:clamp(2.75rem,7vw,4.75rem);
    /* 8px spacing scale */
    --sp-1:8px; --sp-2:16px; --sp-3:24px; --sp-4:32px; --sp-5:48px; --sp-6:64px; --sp-7:96px;
    --gutter:24px;
    --r-lg:24px; --r-md:16px; --r-sm:12px;
    --ease:cubic-bezier(0.22,1,0.36,1);
    --t-fast:180ms; --t-med:300ms;
    /* palette — light */
    --bg:#fbfbfd; --bg-2:#f5f5f7; --card:#ffffff; --fill:#f2f2f4;
    --hair:rgba(0,0,0,0.08); --hair-2:rgba(0,0,0,0.05);
    --txt:#1d1d1f; --txt-2:#5f5f64; --txt-3:#6b6b70;
    --accent:#b4502d; --accent-soft:rgba(191,90,54,0.10); --accent-ring:rgba(191,90,54,0.28);
    --cta:#b5532f; --cta-2:#a24424;
    --shadow:0 1px 2px rgba(0,0,0,0.04), 0 12px 32px rgba(0,0,0,0.05);
    --sev2:#964307; --sev3:#b03a0a; --sev4:#b91c1c;
    --del-fg:#a52f1e; --add-fg:#16662d; --ok:#248a3d; --warn:#8f4b00; --bad:#d70015;
    --glass:rgba(251,251,253,0.72);
    /* legacy aliases still referenced by inline styles / components */
    --card-bg:var(--card); --card-bdr:var(--hair); --text-h:var(--txt); --text-b:var(--txt); --text-m:var(--txt-2);
    --input-bg:var(--fill); --input-bdr:transparent; --input-txt:var(--txt);
    --out-bg:var(--card); --code-bg:var(--fill); --code-txt:var(--txt);
    --chip-bg:var(--card); --chip-bdr:var(--hair);
    --loader-bg:var(--card); --loader-title:var(--txt); --loader-sub:var(--txt-2);
    color-scheme:light;
}
@media (prefers-color-scheme: dark) {
    :root:not([data-sangha-theme="light"]) body:not(:has(#dmchk:checked)) {
    --bg:#000000; --bg-2:#0b0b0c; --card:#1c1c1e; --fill:#2c2c2e;
    --hair:rgba(255,255,255,0.12); --hair-2:rgba(255,255,255,0.07);
    --txt:#f5f5f7; --txt-2:#abaab0; --txt-3:#9d9da3;
    --accent:#f0956f; --accent-soft:rgba(240,149,111,0.16); --accent-ring:rgba(240,149,111,0.38);
    --cta:#b8562f; --cta-2:#a54a26; --shadow:0 0 0 1px rgba(255,255,255,0.02);
    --sev2:#fbbf24; --sev3:#fb923c; --sev4:#f87171; --del-fg:#ff8a80; --add-fg:#7ee2a0;
    --glass:rgba(0,0,0,0.62);
    --av-bs:22%; --av-bl:24%; --av-fs:55%; --av-fl:80%;
    color-scheme:dark;
    }
    :root:not([data-sangha-theme="light"]):has(body:not(:has(#dmchk:checked))) { color-scheme:dark; }
}
body:has(#dmchk:checked) {
    --bg:#000000; --bg-2:#0b0b0c; --card:#1c1c1e; --fill:#2c2c2e;
    --hair:rgba(255,255,255,0.12); --hair-2:rgba(255,255,255,0.07);
    --txt:#f5f5f7; --txt-2:#abaab0; --txt-3:#9d9da3;
    --accent:#f0956f; --accent-soft:rgba(240,149,111,0.16); --accent-ring:rgba(240,149,111,0.38);
    --cta:#b8562f; --cta-2:#a54a26; --shadow:0 0 0 1px rgba(255,255,255,0.02);
    --sev2:#fbbf24; --sev3:#fb923c; --sev4:#f87171; --del-fg:#ff8a80; --add-fg:#7ee2a0;
    --glass:rgba(0,0,0,0.62);
    --av-bs:22%; --av-bl:24%; --av-fs:55%; --av-fl:80%;
    color-scheme:dark;
}

html { font-size:16px; transition:font-size var(--t-fast) var(--ease); -webkit-text-size-adjust:100%; }
html:has(#fsSmall:checked) { font-size:14px; }
html:has(#fsLarge:checked) { font-size:18px; }
html:has(#dmchk:checked) { color-scheme:dark; }
/* hidden state inputs + fixed top bar must not occupy layout space */
div[data-testid="stElementContainer"]:has(#dmchk), div.element-container:has(#dmchk) { display:none; }
div[data-testid="stElementContainer"]:has(.topbar), div.element-container:has(.topbar) { height:0; min-height:0; margin:0 0 -1rem; overflow:visible; }
html, body, .stApp { font-family:var(--font) !important; }
.stApp { background:var(--bg) !important; color:var(--txt); -webkit-font-smoothing:antialiased; }
code, pre, pre * , .stCode * { font-family:var(--mono) !important; }
.stApp [data-testid="stMarkdownContainer"] :is(p,li,h1,h2,h3,h4,strong,em) { color:var(--txt); }
.stApp [data-testid="stCaptionContainer"], .stApp [data-testid="stCaptionContainer"] * { color:var(--txt-2) !important; font-size:var(--fs-1); line-height:1.5;  opacity:1 !important; }
.stApp [data-testid="stMarkdownContainer"] p { line-height:1.55; }
.main .block-container, [data-testid="stMainBlockContainer"], .block-container {
    max-width:1040px !important; margin:0 auto;
    padding:calc(56px + var(--sp-5)) var(--gutter) var(--sp-7) !important;
}
#MainMenu, footer, header, [data-testid="stToolbar"], [data-testid="stDecoration"] { visibility:hidden; height:0; }
* { box-sizing:border-box; }
::selection { background:var(--accent-ring); color:inherit; }
meta { display:none; }

/* ── STICKY FROSTED TOP BAR (app name + team + display controls) ── */
.topbar {
    position:fixed; top:0; left:0; right:0; z-index:99990; height:56px;
    background:var(--glass);
    -webkit-backdrop-filter:blur(20px) saturate(180%); backdrop-filter:blur(20px) saturate(180%);
    border-bottom:1px solid var(--hair);
}
.topbar-in { max-width:1040px; margin:0 auto; height:100%; padding:0 var(--gutter); display:flex; align-items:center; gap:var(--sp-2); }
.tb-brand { display:flex; align-items:center; gap:10px; font-weight:600; font-size:0.9375rem; letter-spacing:-0.01em; color:var(--txt); }
.tb-brand svg { width:20px; height:20px; color:var(--accent); }
.tb-team {
    font-size:var(--fs-1); color:var(--txt-2); background:var(--fill); border-radius:999px;
    padding:4px 12px; max-width:38vw; overflow:hidden; text-overflow:ellipsis; white-space:nowrap;
}
.tb-spacer { flex:1; }
#dmchk { display:none; }
.dm-label {
    position:relative; width:46px; height:28px; border-radius:999px; cursor:pointer; flex-shrink:0;
    background:var(--fill); border:1px solid var(--hair); display:block;
    transition:background var(--t-med) var(--ease);
}
.dm-label::after {
    content:''; position:absolute; top:2px; left:2px; width:22px; height:22px; border-radius:50%;
    background:#fff; box-shadow:0 1px 3px rgba(0,0,0,0.25);
    transition:transform var(--t-med) var(--ease);
}
body:has(#dmchk:checked) .dm-label { background:var(--cta); border-color:transparent; }
body:has(#dmchk:checked) .dm-label::after { transform:translateX(18px); }
.dm-label:focus-visible { outline:2px solid var(--accent); outline-offset:2px; }
.fs-toggle { display:flex; gap:2px; background:var(--fill); border-radius:999px; padding:2px; }
#fsSmall, #fsNormal, #fsLarge { display:none; }
.fs-btn {
    min-width:30px; height:24px; padding:0 4px; display:flex; align-items:center; justify-content:center;
    border-radius:999px; font-size:0.72rem; font-weight:600; cursor:pointer; color:var(--txt-2);
    transition:background var(--t-fast) var(--ease), color var(--t-fast) var(--ease);
}
body:has(#fsSmall:checked) label[for="fsSmall"], body:has(#fsNormal:checked) label[for="fsNormal"], body:has(#fsLarge:checked) label[for="fsLarge"] {
    background:var(--card); color:var(--txt); box-shadow:0 1px 2px rgba(0,0,0,0.12);
}

/* ── HERO ── */
.hero-section { text-align:center; margin:var(--sp-4) auto var(--sp-5); position:relative; z-index:1; max-width:760px; }
.hero-glow {
    position:absolute; z-index:-1; left:50%; top:-40px; width:560px; max-width:100%; height:300px; transform:translateX(-50%);
    background:radial-gradient(closest-side, var(--accent-soft), transparent); filter:blur(28px); pointer-events:none;
}
.eyebrow {
    font-size:0.75rem; font-weight:600; letter-spacing:0.12em; text-transform:uppercase; color:var(--txt-3);
    margin-bottom:var(--sp-1);
}
.main-title {
    font-size:var(--fs-5); font-weight:600; letter-spacing:-0.045em; line-height:1.04; color:var(--txt);
    margin:var(--sp-1) 0 var(--sp-2);
}
.main-title .accent-grad {
    background:linear-gradient(120deg,#d9805a,#b4502d 55%,#8f3f22);
    -webkit-background-clip:text; background-clip:text; -webkit-text-fill-color:transparent; color:transparent;
}
.main-subtitle { color:var(--txt-2) !important; font-size:1.3125rem; font-weight:400; line-height:1.45; letter-spacing:-0.012em; max-width:600px; margin:0 auto; }
.sangha-meaning { margin-top:var(--sp-3); font-size:var(--fs-1); color:var(--txt-3) !important; letter-spacing:0.01em; }

/* ── SECTION HEADINGS ── */
.section-head { margin:var(--sp-6) 0 var(--sp-3); }
.section-head h2 { font-size:var(--fs-4); font-weight:600; letter-spacing:-0.03em; line-height:1.1; margin:0; color:var(--txt); }
.section-head p { margin:var(--sp-1) 0 0; color:var(--txt-2); font-size:1.0625rem; line-height:1.5; max-width:640px; }
.divider { height:1px; background:var(--hair); margin:var(--sp-5) 0 0; border:0; }
.custom-card { background:transparent; border:0; box-shadow:none; padding:0; margin:0; }

/* ── CARDS (shared surface) ── */
.surface, .member-chips, .stats-row, .health-badge, .diff-panel, .hist-card, .trend-card, .empty-state, .loader-wrap, .notice, .badge-pill {
    background:var(--card); border:1px solid var(--hair); border-radius:var(--r-lg); box-shadow:var(--shadow);
}

/* ── INPUTS — filled, borderless, soft accent focus ring ── */
.stApp [data-testid="stWidgetLabel"] p, .stApp label p {
    font-size:var(--fs-1) !important; font-weight:500 !important; color:var(--txt-2) !important;
    letter-spacing:0 !important; text-transform:none !important;
}
[data-baseweb="input"], [data-baseweb="base-input"], [data-baseweb="textarea"], [data-baseweb="select"] > div, div[data-testid="stDateInput"] > div > div {
    background:var(--fill) !important; border:1px solid transparent !important; border-radius:var(--r-md) !important;
    box-shadow:none !important; transition:box-shadow var(--t-fast) var(--ease), border-color var(--t-fast) var(--ease) !important;
}
[data-baseweb="input"]:focus-within, [data-baseweb="base-input"]:focus-within, [data-baseweb="textarea"]:focus-within, [data-baseweb="select"] > div:focus-within {
    border-color:var(--accent) !important; box-shadow:0 0 0 4px var(--accent-soft) !important;
}
.stTextArea textarea, .stTextInput input, [data-baseweb="select"] input, div[data-testid="stDateInput"] input {
    background:transparent !important; color:var(--txt) !important; -webkit-text-fill-color:var(--txt) !important;
    font-size:1rem !important; font-weight:400 !important; border:0 !important; box-shadow:none !important;
}
[data-baseweb="select"] div, [data-baseweb="select"] span, [data-baseweb="select"] p, [data-baseweb="select"] svg { color:var(--txt) !important; -webkit-text-fill-color:var(--txt); }
[data-baseweb="select"] svg { fill:var(--txt-2) !important; }
.stTextArea textarea { min-height:240px !important; line-height:1.7 !important; padding:var(--sp-2) var(--sp-3) !important; }
[data-testid="stTextArea"] [data-baseweb="textarea"] { border-radius:var(--r-lg) !important; }
.stTextArea textarea::placeholder, .stTextInput input::placeholder { color:var(--txt-3) !important; -webkit-text-fill-color:var(--txt-3) !important; opacity:1 !important; }
div[data-testid="stSelectbox"] div[aria-disabled="true"], div[data-testid="stSelectbox"] div[aria-disabled="true"] * { opacity:0.9 !important; }
span[data-baseweb="tag"] { background:var(--accent-soft) !important; color:var(--accent) !important; border-radius:999px !important; }
span[data-baseweb="tag"] * { color:var(--accent) !important; }
/* dropdown popovers are portaled to <body> */
div[data-baseweb="popover"] > div, div[data-baseweb="popover"] ul, div[data-baseweb="menu"] {
    background:var(--card) !important; border:1px solid var(--hair) !important; border-radius:var(--r-md) !important; box-shadow:var(--shadow) !important;
}
div[data-baseweb="popover"] li, div[data-baseweb="menu"] li, div[data-baseweb="popover"] [role="option"], div[data-baseweb="popover"] li *, div[data-baseweb="popover"] [role="option"] * {
    color:var(--txt) !important; -webkit-text-fill-color:var(--txt) !important; background:transparent !important;
}
div[data-baseweb="popover"] li:hover, div[data-baseweb="popover"] [role="option"]:hover, div[data-baseweb="popover"] li[aria-selected="true"] { background:var(--fill) !important; }
div[data-baseweb="calendar"], div[data-baseweb="calendar"] * { background-color:var(--card); color:var(--txt); }

/* ── SEGMENTED CONTROL (radio) — slim iOS look. Supports the react-aria markup (newer
   Streamlit) and the baseweb markup (older); if neither matches it stays a normal radio. ── */
div[data-testid="stRadio"] [role="radiogroup"], div[data-testid="stRadioGroup"] {
    display:inline-flex !important; flex-direction:row !important; flex-wrap:nowrap; gap:2px !important; background:var(--fill); padding:3px; border-radius:999px; max-width:100%; overflow-x:auto; scrollbar-width:none; width:fit-content;
}
div[data-testid="stRadio"] [role="radiogroup"]::-webkit-scrollbar { display:none; }
div[data-testid="stRadio"] label[data-baseweb="radio"], label[data-testid="stRadioOption"] {
    margin:0 !important; padding:6px 16px !important; border-radius:999px; cursor:pointer; white-space:nowrap;
    transition:background var(--t-fast) var(--ease), box-shadow var(--t-fast) var(--ease);
}
div[data-testid="stRadio"] label[data-baseweb="radio"] > div:first-child, label[data-testid="stRadioOption"] > div > div:first-child { display:none !important; }
div[data-testid="stRadio"] label p, label[data-testid="stRadioOption"] p { margin:0; font-size:0.875rem !important; font-weight:500 !important; color:var(--txt-2) !important; }
div[data-testid="stRadio"] label[data-baseweb="radio"]:has(input:checked), label[data-testid="stRadioOption"][data-selected="true"], label[data-testid="stRadioOption"]:has(input:checked) { background:var(--card); box-shadow:0 1px 3px rgba(0,0,0,0.14); }
div[data-testid="stRadio"] label:has(input:checked) p, label[data-testid="stRadioOption"][data-selected="true"] p { color:var(--txt) !important; }

/* ── TOGGLES / CHECKBOXES ── */
.stCheckbox label p { color:var(--txt) !important; font-weight:400 !important; font-size:0.95rem !important; }
label[data-baseweb="checkbox"] > span:first-child { transition:background var(--t-fast) var(--ease); }
div[data-testid="stCheckbox"] label[data-baseweb="checkbox"]:has(input:checked) > span:first-child { background:var(--cta) !important; border-color:var(--cta) !important; }
div[data-testid="stToggle"] label[data-baseweb="checkbox"]:has(input:checked) > div:first-child { background:var(--cta) !important; }
div[data-testid="stToggle"] label[data-baseweb="checkbox"] > div:first-child { box-shadow:none; }
/* Streamlit <=1.4x renders st.toggle as data-testid="stCheckbox" with a div track (checkbox uses a span):
   match by structure so the checked track uses the brand CTA colour instead of the default red. */
div[data-testid="stCheckbox"] label[data-baseweb="checkbox"]:has(input:checked) > div:first-child { background:var(--cta) !important; }
div[data-testid="stCheckbox"] label[data-baseweb="checkbox"] > div:first-child { box-shadow:none; }
label[data-baseweb="checkbox"] { align-items:center; }
[data-baseweb="slider"] [role="slider"] { background:var(--cta) !important; box-shadow:none !important; }

/* ── BUTTONS ──
   Default (.stButton > button) is the calm compact secondary. The ONE primary CTA is
   targeted by kind="primary" (+ its st-key) and rendered as a centered Apple pill. */
.stButton > button, [data-testid="stDownloadButton"] button {
    background:var(--fill) !important; color:var(--accent) !important; border:0 !important; border-radius:999px !important;
    padding:0.5rem 1.1rem !important; min-height:40px; font-size:0.9rem !important; font-weight:500 !important;
    letter-spacing:0 !important; text-transform:none; margin:0.15rem 0; box-shadow:none !important;
    transition:transform var(--t-fast) var(--ease), background var(--t-fast) var(--ease), opacity var(--t-fast) var(--ease) !important;
}
.stButton > button p, [data-testid="stDownloadButton"] button p { color:inherit !important; font-weight:500 !important; font-size:inherit !important; }
.stButton > button:hover, [data-testid="stDownloadButton"] button:hover { background:var(--accent-soft) !important; transform:none !important; }
.stButton > button:active, [data-testid="stDownloadButton"] button:active { transform:scale(0.98) !important; }
div[class*="st-key-sec_"] button { padding:0.5rem 1.1rem !important; font-size:0.875rem !important; border-radius:999px !important; display:inline-flex !important; margin:0.15rem 0 !important; }
div.stButton:has(button[kind="primary"]), div[class*="st-key-generate_btn"] { display:flex !important; justify-content:center !important; margin:var(--sp-4) 0 var(--sp-2); }
div[class*="st-key-generate_btn"] > div { width:auto !important; }
.stButton > button[kind="primary"], .stButton > button[data-testid="stBaseButton-primary"], .stButton > button[data-testid="baseButton-primary"], div[class*="st-key-generate_btn"] button {
    background:linear-gradient(180deg,var(--cta),var(--cta-2)) !important; color:#fff !important;
    min-width:min(280px,100%); max-width:100%; min-height:52px; padding:0.85rem 2.5rem !important;
    font-size:1.0625rem !important; font-weight:500 !important; letter-spacing:-0.005em !important;
    box-shadow:0 1px 2px rgba(0,0,0,0.12), 0 8px 24px var(--accent-soft) !important; display:block; margin:0 auto;
}
.stButton > button[kind="primary"]:hover, .stButton > button[data-testid="stBaseButton-primary"]:hover, div[class*="st-key-generate_btn"] button:hover { background:linear-gradient(180deg,var(--cta),var(--cta-2)) !important; filter:brightness(1.06); }
.stButton > button[kind="primary"] p, div[class*="st-key-generate_btn"] button p { color:#fff !important; font-size:1.0625rem !important; }
.action-btn {
    display:inline-flex; align-items:center; gap:6px; background:var(--fill); border-radius:999px;
    padding:0.4rem 1rem; font-size:0.875rem; font-weight:500; color:var(--accent) !important; text-decoration:none;
    transition:background var(--t-fast) var(--ease), transform var(--t-fast) var(--ease);
}
.action-btn:hover { background:var(--accent-soft); }
.action-btn:active { transform:scale(0.98); }
button:focus-visible, input:focus-visible, textarea:focus-visible, a:focus-visible { outline:2px solid var(--accent) !important; outline-offset:2px !important; }

/* ── EXPANDERS (Customize, history, roster ...) ── */
details, [data-testid="stExpander"] details {
    background:var(--card) !important; border:1px solid var(--hair) !important; border-radius:var(--r-lg) !important;
    box-shadow:var(--shadow); padding:0.25rem var(--sp-2) !important; margin-bottom:var(--sp-2) !important;
}
[data-testid="stExpander"] { border:0 !important; background:transparent !important; }
details summary { color:var(--txt) !important; font-weight:500 !important; cursor:pointer; padding:0.55rem 0 !important; }
details summary p { color:var(--txt) !important; font-weight:500 !important; font-size:1rem !important; }
details summary svg { color:var(--txt-3) !important; }
details[open] > summary { border-bottom:1px solid var(--hair-2); margin-bottom:var(--sp-2); }

/* ── OUTPUT TABS — sliding pill segmented bar ── */
[data-testid="stTabs"] [data-baseweb="tab-list"] {
    position:relative; display:flex; gap:2px; background:var(--fill); padding:4px; border-radius:999px; width:fit-content; max-width:100%;
    overflow-x:auto; scrollbar-width:none; border:0 !important; margin-bottom:var(--sp-3);
}
[data-testid="stTabs"] [data-baseweb="tab-list"]::-webkit-scrollbar { display:none; }
[data-testid="stTabs"] button[role="tab"] {
    position:relative; z-index:1; background:transparent !important; border-radius:999px !important; padding:6px 16px !important; height:auto !important; min-height:36px;
    color:var(--txt-2) !important; flex-shrink:0; transition:color var(--t-fast) var(--ease);
}
[data-testid="stTabs"] button[role="tab"] p { font-size:0.875rem !important; font-weight:500 !important; color:inherit !important; margin:0; white-space:nowrap; }
[data-testid="stTabs"] button[role="tab"][aria-selected="true"] { color:var(--txt) !important; }
[data-testid="stTabs"] [data-baseweb="tab-highlight"] {
    top:4px !important; bottom:4px !important; height:auto !important; background:var(--card) !important; border-radius:999px !important;
    box-shadow:0 1px 3px rgba(0,0,0,0.14); z-index:0 !important; transition:transform var(--t-med) var(--ease), width var(--t-med) var(--ease) !important;
}
[data-testid="stTabs"] [data-baseweb="tab-border"] { display:none !important; }
[data-testid="stTabs"] [data-baseweb="tab-panel"] { padding-top:0 !important; }

/* ── OUTPUT BLOCKS ── */
@keyframes blockReveal { from{opacity:0;transform:translateY(12px)} to{opacity:1;transform:translateY(0)} }
.colored-block { padding:0 0 var(--sp-2); background:transparent; border:0; box-shadow:none; animation:blockReveal 0.5s var(--ease) both; position:relative; }
.block-title { font-size:var(--fs-3); font-weight:600; letter-spacing:-0.02em; margin:0; display:flex; align-items:center; justify-content:space-between; gap:12px; color:var(--txt); }
.block-title-text { display:flex; align-items:center; gap:12px; }
.block-icon-badge { width:40px; height:40px; border-radius:50%; flex-shrink:0; display:inline-flex; align-items:center; justify-content:center; background:var(--accent-soft); color:var(--accent); }
.block-icon-badge svg { width:20px; height:20px; stroke:currentColor; fill:none; stroke-width:1.75; stroke-linecap:round; stroke-linejoin:round; }
.narrative-title,.chat-title,.whatsapp-title,.email-title,.tomorrow-title,.blocker-title { color:var(--txt); }
.colored-block .stTextArea textarea, [data-testid="stTabs"] .stTextArea textarea { min-height:120px !important; font-family:var(--mono) !important; font-size:0.875rem !important; line-height:1.7 !important; }
pre, [data-testid="stCode"] pre {
    border-radius:var(--r-md) !important; background:var(--fill) !important; border:0 !important; padding:var(--sp-2) var(--sp-3) !important;
    color:var(--txt) !important; font-size:0.875rem !important; line-height:1.7 !important;
}
[data-testid="stCode"] { border-radius:var(--r-md); }
pre code, pre span { color:var(--txt) !important; background:transparent !important; }

/* ── SECTION: MEMBERS (contacts-style list) ── */
.member-chips { display:block; margin-top:var(--sp-2); padding:var(--sp-1) 0; overflow:hidden; }
.member-chip { display:flex; align-items:flex-start; gap:var(--sp-2); padding:var(--sp-2) var(--sp-3); position:relative; animation:fadeUp 0.5s var(--ease) both; min-height:44px; }
.member-chip + .member-chip::before { content:''; position:absolute; top:0; right:0; left:calc(var(--sp-3) + 44px + var(--sp-2)); height:1px; background:var(--hair-2); }
.mc-avatar {
    width:44px; height:44px; border-radius:50%; flex-shrink:0; display:flex; align-items:center; justify-content:center; font-weight:600; font-size:1.0625rem;
    background:hsl(var(--h,20) var(--av-bs,28%) var(--av-bl,90%)); color:hsl(var(--h,20) var(--av-fs,38%) var(--av-fl,30%));
}
.mc-main { min-width:0; flex:1; }
.mc-top { display:flex; align-items:center; flex-wrap:wrap; gap:8px; }
.chip-name { font-weight:600; font-size:1.0625rem; letter-spacing:-0.01em; color:var(--txt); }
.chip-role { font-size:var(--fs-1); color:var(--txt-2); }
.mc-badges { display:flex; flex-wrap:wrap; gap:6px; margin-top:6px; }
.pill { display:inline-flex; align-items:center; gap:4px; border-radius:999px; padding:2px 10px; font-size:0.75rem; font-weight:500; background:var(--fill); color:var(--txt-2); line-height:1.6; }
.pill-block { background:rgba(255,159,10,0.16); color:var(--sev2); }
.pill-out { background:var(--accent-soft); color:var(--accent); }
.chip-block { font-size:0.8125rem; color:var(--txt-2); margin-top:6px; line-height:1.5; }
.chip-tasks { font-size:var(--fs-1); color:var(--txt-2); }
.mention-pill { display:inline-flex; align-items:center; background:var(--accent-soft); border-radius:999px; padding:0 8px; font-weight:500; color:var(--accent) !important; font-size:0.92em; }

/* ── STATS strip ── */
.stats-row { display:grid; grid-template-columns:repeat(3,1fr); margin:var(--sp-4) 0 0; padding:var(--sp-4) 0; }
.stat-chip { text-align:center; padding:0 var(--sp-2); background:transparent; border:0; }
.stat-chip + .stat-chip { border-left:1px solid var(--hair); }
.stat-val { font-size:clamp(2.5rem,7vw,3.75rem); font-weight:300; letter-spacing:-0.04em; line-height:1; color:var(--txt); display:inline-block; font-variant-numeric:tabular-nums; }
.stat-lbl { font-size:var(--fs-1); font-weight:500; color:var(--txt-2); margin-top:var(--sp-1); letter-spacing:0; text-transform:none; }

/* ── HEALTH gauge + shared badges ── */
.badge-pill { display:block; padding:var(--sp-2) var(--sp-3); margin-top:var(--sp-2); font-size:0.9375rem; font-weight:400; color:var(--txt); border-radius:var(--r-lg); }
.badge-pill strong { font-weight:600; }
.badge-pill .bp-line { margin-top:6px; font-size:0.875rem; }
.badge-info { background:var(--card); }
.badge-alert { border-color:rgba(255,59,48,0.25); }
.health-badge { display:flex; align-items:center; gap:var(--sp-3); padding:var(--sp-3); margin-top:var(--sp-2); }
.health-ring { position:relative; width:84px; height:84px; flex-shrink:0; }
.health-ring svg { width:100%; height:100%; transform:rotate(-90deg); }
.health-ring .hr-track { stroke:var(--fill); }
.health-ring .hr-val { transition:stroke-dashoffset 1s var(--ease); animation:ringIn 1.1s var(--ease) both; }
@keyframes ringIn { from{stroke-dashoffset:var(--hr-c)} }
.health-ring .hr-num { position:absolute; inset:0; display:flex; align-items:center; justify-content:center; font-size:1.75rem; font-weight:600; letter-spacing:-0.03em; color:var(--txt); }
.health-label { font-size:1.1875rem; font-weight:600; letter-spacing:-0.015em; color:var(--txt); }
.health-sub { font-size:var(--fs-1); color:var(--txt-2); margin-top:2px; }

/* ── TREND (SVG line chart) ── */
.trend-card { padding:var(--sp-3); margin-top:var(--sp-2); }
.trend-head { display:flex; justify-content:space-between; align-items:baseline; flex-wrap:wrap; gap:8px; }
.trend-legend { display:flex; gap:var(--sp-2); font-size:0.75rem; color:var(--txt-2); }
.trend-legend span { display:inline-flex; align-items:center; gap:6px; }
.trend-legend i { width:8px; height:8px; border-radius:50%; display:inline-block; }
.trend-plot { position:relative; margin-top:var(--sp-2); }
.trend-plot svg { width:100%; height:auto; display:block; overflow:visible; }
.trend-line { fill:none; stroke-width:2; stroke-linecap:round; stroke-linejoin:round; stroke-dasharray:1; animation:drawLine 1.2s var(--ease) backwards; }
@keyframes drawLine { from{stroke-dashoffset:1} to{stroke-dashoffset:0} }
.trend-grid { stroke:var(--hair-2); stroke-width:1; }
.trend-x { position:relative; height:18px; margin-top:6px; }
.trend-x span { position:absolute; transform:translateX(-50%); font-size:0.6875rem; color:var(--txt-3); white-space:nowrap; }
.trend-x span:first-child { transform:none; } .trend-x span:last-child { transform:translateX(-100%); }

/* ── DIFF PANEL ── */
.diff-panel { margin-top:var(--sp-2); padding:var(--sp-3); }
.diff-panel-title { font-weight:600; font-size:var(--fs-2); letter-spacing:-0.01em; color:var(--txt); margin-bottom:var(--sp-2); }
.diff-row { margin-bottom:var(--sp-2); } .diff-row:last-child { margin-bottom:0; }
.diff-name { font-size:var(--fs-1); font-weight:500; color:var(--txt-2); margin-bottom:6px; }
.diff-cols { display:flex; align-items:stretch; gap:var(--sp-1); flex-wrap:wrap; }
.diff-col { flex:1; min-width:200px; font-size:0.875rem; line-height:1.5; border-radius:var(--r-sm); padding:var(--sp-1) var(--sp-2); }
.diff-label { display:block; font-size:0.6875rem; font-weight:600; letter-spacing:0.08em; text-transform:uppercase; margin-bottom:2px; color:var(--txt-3); }
.diff-yesterday { background:var(--fill); color:var(--txt-2); }
.diff-today { background:var(--accent-soft); color:var(--txt); }
.diff-arrow { align-self:center; color:var(--txt-3); flex-shrink:0; }
@media (max-width:600px) { .diff-arrow { transform:rotate(90deg); } }
del.diff-del, .diff-del { background:rgba(255,59,48,0.12); color:var(--del-fg); text-decoration:line-through; border-radius:6px; padding:0 4px; font-weight:400; }
mark.diff-add, .diff-add { background:rgba(52,199,89,0.18); color:var(--add-fg); border-radius:6px; padding:0 4px; font-weight:500; }

/* ── HISTORY ── */
.timeline-wrap { position:relative; display:flex; overflow-x:auto; padding:var(--sp-3) var(--sp-1) var(--sp-1); margin-bottom:var(--sp-2); scrollbar-width:thin; }
.timeline-line { position:absolute; top:calc(var(--sp-3) + 5px); left:var(--sp-3); right:var(--sp-3); height:1px; background:var(--hair); }
.tl-node { position:relative; flex:0 0 96px; text-align:center; z-index:1; }
.tl-dot { width:10px; height:10px; border-radius:50%; background:var(--accent); margin:0 auto var(--sp-1); border:2px solid var(--bg); transition:transform var(--t-fast) var(--ease); }
.tl-node:hover .tl-dot { transform:scale(1.3); }
.tl-label { font-size:0.75rem; font-weight:500; color:var(--txt); white-space:nowrap; }
.tl-sub { font-size:0.6875rem; color:var(--txt-3); }
.hist-card { padding:var(--sp-2) var(--sp-3); margin-bottom:var(--sp-1); display:flex; justify-content:space-between; align-items:flex-start; gap:12px; box-shadow:none; }
.hist-date { font-size:var(--fs-2); font-weight:600; letter-spacing:-0.01em; color:var(--txt); }
.hist-meta { font-size:var(--fs-1); color:var(--txt-2); margin-top:4px; }

/* ── NOTICES / EMPTY / TOKEN ── */
.notice { margin:0 0 var(--sp-3); padding:var(--sp-2) var(--sp-3); font-size:0.9375rem; text-align:center; box-shadow:none; color:var(--txt-2); }
.notice strong { color:var(--txt); font-weight:600; }
.empty-state { text-align:center; padding:var(--sp-5) var(--sp-3); margin-top:var(--sp-3); box-shadow:none; background:transparent; border:1px dashed var(--hair); animation:fadeUp 0.6s var(--ease) both; }
.empty-state-icon { display:none; }
.empty-state-decor { position:relative; width:100%; max-width:180px; height:70px; margin:0 auto var(--sp-1); }
.empty-state-title { font-weight:600; font-size:1.1875rem; letter-spacing:-0.015em; color:var(--txt); margin-bottom:6px; }
.empty-state-sub { font-size:0.9375rem; color:var(--txt-2); max-width:440px; margin:0 auto; line-height:1.5; }
.token-row { text-align:center; margin:var(--sp-4) 0 0; }
.token-badge { display:inline-block; background:transparent; color:var(--txt-3) !important; font-weight:400; font-size:var(--fs-1); }

/* ── LOADER (calm; crossfades between stages) ── */
@keyframes loaderFadeIn { from{opacity:0;transform:translateY(8px)} to{opacity:1;transform:translateY(0)} }
@keyframes shimmer { 0%{background-position:200% 0} 100%{background-position:-200% 0} }
@keyframes dotPop { from{transform:scale(0.5);opacity:0} to{transform:scale(1);opacity:1} }
@keyframes pulseSoft { 0%,100%{transform:scale(1);opacity:1} 50%{transform:scale(1.06);opacity:0.85} }
.loader-wrap { padding:var(--sp-5) var(--sp-4); text-align:center; max-width:560px; margin:var(--sp-3) auto; animation:loaderFadeIn 0.5s var(--ease) both; position:relative; overflow:hidden; }
.loader-emoji { width:72px; height:72px; margin:0 auto var(--sp-2); border-radius:50%; background:var(--accent-soft); display:flex; align-items:center; justify-content:center; font-size:2rem; animation:pulseSoft 2.4s ease-in-out infinite; }
.loader-title { font-size:var(--fs-3); font-weight:600; letter-spacing:-0.02em; margin-bottom:6px; color:var(--txt); }
.loader-sub { font-size:0.9375rem; margin-bottom:var(--sp-3); color:var(--txt-2); }
.loader-dots { display:flex; justify-content:center; gap:8px; margin-bottom:var(--sp-3); }
.ld { width:8px; height:8px; border-radius:50%; background:var(--fill); transition:background var(--t-med) var(--ease); }
.lactive { background:var(--cta); animation:dotPop 0.4s var(--ease) both; }
.ldone { background:var(--accent-ring); }
.loader-bar-bg { height:4px; border-radius:99px; background:var(--fill); overflow:hidden; margin-bottom:var(--sp-1); }
.loader-bar-fg { height:100%; border-radius:99px; background:linear-gradient(90deg,var(--cta),#e08a68,var(--cta)); background-size:200% 100%; animation:shimmer 1.8s linear infinite; transition:width 0.6s var(--ease); }
.loader-pct { font-size:0.75rem; font-weight:500; color:var(--txt-3); }
.loader-micro { position:relative; height:1.2rem; margin:0.4rem 0 var(--sp-2); }
.loader-micro-item { position:absolute; left:0; right:0; text-align:center; font-size:0.875rem; color:var(--txt-3); opacity:0; animation-name:microCycle; animation-timing-function:ease-in-out; animation-iteration-count:infinite; }
@keyframes microCycle { 0%{opacity:0} 3%{opacity:1} 16%{opacity:1} 20%{opacity:0} 100%{opacity:0} }

/* ── MOTION: page-load orchestration + scroll reveal ── */
@keyframes fadeUp { from{opacity:0;transform:translateY(14px)} to{opacity:1;transform:translateY(0)} }
.hero-section > * { animation:fadeUp 0.8s var(--ease) both; }
.hero-section > .eyebrow { animation-delay:0.02s; } .hero-section > .main-title { animation-delay:0.1s; }
.hero-section > .main-subtitle { animation-delay:0.2s; } .hero-section > .sangha-meaning { animation-delay:0.3s; }
/* (stagger fade-in on every expander/textarea removed — perf) */
@supports (animation-timeline: view()) {
    @keyframes revealIn { from{opacity:0;transform:translateY(24px)} to{opacity:1;transform:translateY(0)} }
    .reveal { animation:revealIn linear both; animation-timeline:view(); animation-range:entry 0% entry 35%; }
    @keyframes heroDrift { to{transform:translateX(-50%) translateY(60px)} }
    .hero-glow { animation:heroDrift linear both; animation-timeline:scroll(root); animation-range:0 600px; }
}

/* ── SCROLLBAR ── */
::-webkit-scrollbar { width:10px; height:10px; }
::-webkit-scrollbar-track { background:transparent; }
::-webkit-scrollbar-thumb { background:var(--accent-ring); border-radius:99px; border:2px solid transparent; background-clip:padding-box; }
::-webkit-scrollbar-thumb:hover { background:var(--accent); background-clip:padding-box; border:2px solid transparent; }
* { scrollbar-color:var(--accent-ring) transparent; }

/* ── native alerts / dataframe polish ── */
[data-testid="stAlert"] { border-radius:var(--r-md); border:1px solid var(--hair); }
[data-testid="stDataFrame"] { border-radius:var(--r-md); overflow:hidden; border:1px solid var(--hair); }
hr { border-color:var(--hair) !important; }
[data-testid="stToast"], div[data-baseweb="toast"] { border-radius:var(--r-md) !important; }

/* ── PRINT ── */
@media print {
    .stButton, #dmchk, .dm-label, .topbar { display:none !important; }
    .stApp { background:#fff !important; }
    .colored-block, .surface, .member-chips, .stats-row { box-shadow:none !important; }
}

/* ── TABLET / MOBILE ── */
@media (max-width:768px) {
    :root { --gutter:16px; }
    .hero-section { margin-top:var(--sp-2); }
    .main-subtitle { font-size:1.125rem; }
    .section-head { margin-top:var(--sp-5); } .section-head h2 { font-size:1.75rem; }
    .tb-team { max-width:30vw; }
    .loader-wrap { padding:var(--sp-4) var(--sp-2); }
}
@media (max-width:640px) {
    .main .block-container, [data-testid="stMainBlockContainer"], .block-container { padding-left:var(--gutter) !important; padding-right:var(--gutter) !important; }
    /* edge-to-edge cards */
    .member-chips, .stats-row, .health-badge, .diff-panel, .hist-card, .trend-card, .notice, .badge-pill, .empty-state {
        margin-left:calc(-1 * var(--gutter)); margin-right:calc(-1 * var(--gutter)); border-radius:0; border-left:0; border-right:0;
    }
    .member-chip { padding:var(--sp-2); } .member-chip + .member-chip::before { left:calc(var(--sp-2) + 44px + var(--sp-2)); }
    .topbar-in { gap:var(--sp-1); } .fs-toggle { display:none; }
    .stat-val { font-size:2.25rem; } .stat-chip { padding:0 var(--sp-1); }
    .stButton > button, [data-testid="stDownloadButton"] button, [data-testid="stTabs"] button[role="tab"], [data-baseweb="input"], [data-baseweb="select"] > div { min-height:44px !important; }
    .stButton > button[kind="primary"], div[class*="st-key-generate_btn"] button { width:100%; }
    div.stButton:has(button[kind="primary"]) { width:100%; }
    .stTextArea textarea { min-height:200px !important; }
    html, body { overflow-x:hidden; }
    .diff-col { min-width:0; flex-basis:100%; }
    .health-badge { gap:var(--sp-2); }
}

/* ── REDUCED MOTION ── */
@media (prefers-reduced-motion: reduce) {
    *, *::before, *::after { animation-duration:0.001ms !important; animation-iteration-count:1 !important; animation-delay:0s !important; transition-duration:0.001ms !important; scroll-behavior:auto !important; }
    .reveal, .hero-glow { animation:none !important; }
}

.stats-row, .member-chips { margin-bottom:var(--sp-2); }
[data-testid="stExpander"] { margin-top:var(--sp-1); }
[data-testid="stRadio"], [data-testid="stMultiSelect"] { margin-top:var(--sp-1); }

div[class*="st-key-generate_btn"] { width:100% !important; }
div[data-testid="stCheckbox"][data-selected="true"] label > div:first-of-type { background:var(--cta) !important; border-color:var(--cta) !important; }
details > summary { background:transparent !important; }
.stTextArea textarea { min-height:280px !important; }
/* react-aria tabs (newer Streamlit) */
[data-testid="stTabs"] [role="tablist"] { position:relative; display:flex; gap:2px; background:var(--fill); padding:4px; border-radius:999px; width:fit-content; max-width:100%; overflow-x:auto; scrollbar-width:none; border:0 !important; margin-bottom:var(--sp-3); }
[data-testid="stTabs"] [role="tablist"]::-webkit-scrollbar { display:none; }
[data-testid="stTab"] { position:relative; isolation:isolate; background:transparent !important; border-radius:999px !important; padding:6px 16px !important; min-height:36px; color:var(--txt-2) !important; flex-shrink:0; cursor:pointer; display:flex; align-items:center; }
[data-testid="stTab"] p { font-size:0.875rem !important; font-weight:500 !important; color:inherit !important; margin:0; white-space:nowrap; }
[data-testid="stTab"][aria-selected="true"] { color:var(--txt) !important; }
[data-testid="stTab"] .react-aria-SelectionIndicator { position:absolute; inset:0; z-index:-1; background:var(--card) !important; border-radius:999px !important; box-shadow:0 1px 3px rgba(0,0,0,0.14); height:auto !important; }
[data-testid="stTabs"] [role="tablist"] > div[style*="height"], [data-testid="stTabs"] [role="tablist"] hr { display:none !important; }
div[data-testid="stTextAreaRootElement"] { border:1px solid transparent !important; box-shadow:none !important; border-radius:var(--r-lg) !important; }
div[data-testid="stTextAreaRootElement"]:focus-within { border-color:var(--accent) !important; box-shadow:0 0 0 4px var(--accent-soft) !important; }
.stTextArea textarea:focus-visible { outline:none !important; }

/* ═══ ROUND 4 — theme-proof widgets ═══
   Streamlit's own theme follows the OS; ours follows the app toggle. Every widget below
   gets BOTH background and text colour from OUR tokens (which switch with the app theme),
   so an OS-dark + app-light (or the reverse) combination can never produce dark-on-dark. */
.stApp, .stApp [data-testid="stAppViewContainer"], .stApp [data-testid="stMain"] { background:var(--bg) !important; color:var(--txt); }
.stApp [data-testid="stWidgetLabel"], .stApp [data-testid="stWidgetLabel"] *, .stApp label > p { color:var(--txt-2) !important; -webkit-text-fill-color:var(--txt-2) !important; opacity:1 !important; }
.stApp [data-testid="stWidgetLabel"] svg, .stApp [data-testid="stTooltipIcon"] svg, .stApp [data-testid="stTooltipHoverTarget"] svg { fill:var(--txt-3) !important; color:var(--txt-3) !important; }
.stApp [data-testid="stCaptionContainer"], .stApp [data-testid="stCaptionContainer"] *, .stApp [data-testid="stWidgetLabel"] + div small, .stApp small { color:var(--txt-2) !important; -webkit-text-fill-color:var(--txt-2) !important; }
.stApp [data-testid="stMarkdownContainer"], .stApp [data-testid="stMarkdownContainer"] :is(p,li,span,h1,h2,h3,h4,strong,em,td,th) { color:var(--txt); }
.stApp [data-testid="stMarkdownContainer"] :is(.eyebrow,.chip-role,.chip-tasks,.hist-meta,.diff-name,.tl-sub,.stat-lbl,.sangha-meaning,.token-badge,.loader-pct,.loader-micro-item,.trend-legend,.trend-legend span) { color:var(--txt-3); }
.stApp [data-testid="stMarkdownContainer"] :is(.chip-block,.diff-yesterday,.health-sub,.empty-state-sub,.notice,.main-subtitle,.section-head p) { color:var(--txt-2); }
.stApp [data-testid="stMarkdownContainer"] .pill-block { color:var(--sev2); }
.stApp [data-testid="stMarkdownContainer"] :is(.pill-out,.mention-pill) { color:var(--accent); }
.stApp [data-testid="stMarkdownContainer"] .diff-del { color:var(--del-fg); } .stApp [data-testid="stMarkdownContainer"] .diff-add { color:var(--add-fg); }
.stApp [data-testid="stMarkdownContainer"] .eyebrow { color:var(--txt-3); }
.diff-label { color:var(--txt-2) !important; }
.trend-plot text, .stApp svg text { fill:var(--txt-2); }
/* text-like inputs: wrapper layers get the fill, the native element stays transparent */
.stApp [data-testid="stTextInputRootElement"], .stApp [data-testid="stNumberInputContainer"], .stApp [data-testid="stTextAreaRootElement"],
.stApp [data-baseweb="input"], .stApp [data-baseweb="base-input"], .stApp [data-baseweb="textarea"], .stApp [data-baseweb="select"] > div,
.stApp [data-baseweb="select"] [data-baseweb="base-input"], .stApp div[data-testid="stDateInput"] > div > div, .stApp [data-testid="stDateInputField"] {
    background-color:var(--fill) !important; background-image:none !important; color:var(--input-txt) !important;
}
.stApp input, .stApp textarea, .stApp [data-baseweb="select"] input {
    background:transparent !important; background-color:transparent !important; color:var(--txt) !important; -webkit-text-fill-color:var(--txt) !important;
    caret-color:var(--accent) !important; opacity:1 !important;
}
.stApp input::placeholder, .stApp textarea::placeholder { color:var(--txt-3) !important; -webkit-text-fill-color:var(--txt-3) !important; opacity:1 !important; }
.stApp input:disabled, .stApp textarea:disabled { color:var(--txt-2) !important; -webkit-text-fill-color:var(--txt-2) !important; opacity:0.7 !important; cursor:not-allowed; }
.stApp [data-baseweb="select"] > div > div, .stApp [data-baseweb="select"] [class*="ValueContainer"] *:not(span[data-baseweb="tag"] *) { color:var(--txt) !important; -webkit-text-fill-color:var(--txt) !important; }
.stApp [data-baseweb="select"] svg, .stApp [data-baseweb="input"] svg, .stApp [data-testid="stNumberInputContainer"] svg { fill:var(--txt-2) !important; color:var(--txt-2) !important; }
.stApp [data-baseweb="select"] [aria-disabled="true"], .stApp [data-baseweb="select"] [aria-disabled="true"] * { color:var(--txt-2) !important; -webkit-text-fill-color:var(--txt-2) !important; }
.stApp [data-testid="stMultiSelect"] div:has(> [data-testid="stMultiSelectTagsContainer"]), .stApp [data-testid="stMultiSelect"] [class*="ComboBox"] > div, .stApp [data-testid="stSelectbox"] [class*="Select"] > div:has(input), .stApp [data-testid="stSelectbox"] div:has(> input) {
    background-color:var(--fill) !important; color:var(--txt) !important; border-radius:var(--r-md) !important;
}
.stApp [data-testid="stMultiSelectTagsContainer"], .stApp [data-testid="stMultiSelectTagsContainer"] > div { background:transparent !important; flex-wrap:wrap !important; gap:4px; }
.stApp [data-testid="stVegaLiteChart"] svg, .stApp [data-testid="stVegaLiteChart"] canvas, .stApp [data-testid="stVegaLiteChart"] { background:transparent !important; }
.stApp [data-testid="stVegaLiteChart"] svg text { fill:var(--txt-2) !important; }
.stApp [data-testid="stVegaLiteChart"] svg path.background { fill:transparent !important; }
.stApp label[data-testid="stRadioOption"][data-selected="true"], .stApp label[data-testid="stRadioOption"]:has(input:checked), .stApp div[data-testid="stRadio"] label[data-baseweb="radio"]:has(input:checked) { background:var(--card) !important; }
.stApp label[data-testid="stRadioOption"]:not([data-selected="true"]):not(:has(input:checked)) { background:transparent !important; }
.stApp label[data-testid="stRadioOption"] p, .stApp label[data-testid="stRadioOption"] * { -webkit-text-fill-color:currentColor; }
.stApp [data-testid="stDateInputField"], .stApp [data-testid="stDateInputField"] * { color:var(--txt) !important; -webkit-text-fill-color:var(--txt) !important; }
/* react-aria dropdowns (Streamlit >=1.4x) — portaled to <body>, so they sit OUTSIDE .stApp and inherit the OS theme unless styled here */
[data-testid$="Dropdown"], [data-testid="stSelectboxVirtualDropdown"], [data-testid="stMultiSelectDropdown"], [role="listbox"] {
    background:var(--card) !important; background-color:var(--card) !important; color:var(--txt) !important; -webkit-text-fill-color:var(--txt) !important;
    border:1px solid var(--hair) !important; border-radius:var(--r-md) !important; box-shadow:var(--shadow) !important;
}
[data-testid$="Dropdown"] *, [role="listbox"] * { color:var(--txt); -webkit-text-fill-color:var(--txt); border-color:var(--hair) !important; }
[data-testid$="Dropdown"] [role="listbox"] { border:0 !important; box-shadow:none !important; background:transparent !important; }
[role="listbox"] [role="option"], [data-testid$="Dropdown"] [role="option"] { background:transparent !important; color:var(--txt) !important; border-radius:var(--r-sm); }
[role="listbox"] [role="option"] *, [data-testid$="Dropdown"] [role="option"] * { background:transparent !important; color:var(--txt) !important; -webkit-text-fill-color:var(--txt) !important; }
[role="listbox"] [role="option"]:hover, [role="listbox"] [role="option"][data-focused="true"], [role="listbox"] [role="option"][data-hovered="true"], [role="listbox"] [role="option"][aria-selected="true"] { background:var(--fill) !important; }
[role="listbox"] [role="option"][aria-disabled="true"], [role="listbox"] [role="option"][aria-disabled="true"] * { color:var(--txt-3) !important; -webkit-text-fill-color:var(--txt-3) !important; }
[data-testid$="Dropdown"] svg { fill:var(--txt-2) !important; color:var(--txt-2) !important; }
[data-testid$="Dropdown"] [data-testid="stSelectboxNoOptions"], [data-testid$="Dropdown"] [role="presentation"] { color:var(--txt-2) !important; }
body:has(#dmchk:checked) [data-testid$="Dropdown"], body:has(#dmchk:checked) [role="listbox"] { color-scheme:dark; }
body:not(:has(#dmchk:checked)) [data-testid$="Dropdown"], body:not(:has(#dmchk:checked)) [role="listbox"] { color-scheme:light; }
.stApp [data-testid="stTextInputRootElement"] *:not(input), .stApp [data-testid="stNumberInputContainer"] *:not(input):not(button) { color:var(--txt-2) !important; -webkit-text-fill-color:var(--txt-2) !important; }
.stApp [data-testid="stMultiSelect"] [class*="ComboBox"], .stApp [data-testid="stMultiSelect"] [data-testid="stMultiSelectTagsContainer"] ~ * { outline:0 !important; }
/* hairline borders: Streamlit's themed 1px border (dark under an OS-dark theme) must not show; focus ring = our accent */
.stApp [data-testid="stTextInputRootElement"], .stApp [data-testid="stNumberInputContainer"], .stApp [data-testid="stTextAreaRootElement"],
.stApp [data-testid="stSelectbox"] [role="group"], .stApp [data-testid="stMultiSelect"] [role="group"], .stApp [data-testid="stDateInputField"], .stApp [data-testid="stDateInput"] [role="group"] {
    border:1px solid transparent !important; border-radius:var(--r-md) !important; outline:0 !important; box-shadow:none !important; background-color:var(--fill) !important;
}
.stApp [data-testid="stTextInputRootElement"]:focus-within, .stApp [data-testid="stNumberInputContainer"]:focus-within, .stApp [data-testid="stTextAreaRootElement"]:focus-within,
.stApp [data-testid="stSelectbox"] [role="group"]:focus-within, .stApp [data-testid="stMultiSelect"] [role="group"]:focus-within, .stApp [data-testid="stDateInput"] [role="group"]:focus-within {
    border-color:var(--accent) !important; box-shadow:0 0 0 4px var(--accent-soft) !important;
}
.stApp [data-testid="stSelectbox"] button svg, .stApp [data-testid="stMultiSelect"] button svg, .stApp [data-testid="stSelectbox"] svg, .stApp [data-testid="stMultiSelect"] > div svg { fill:var(--txt-2) !important; color:var(--txt-2) !important; }
.stApp [data-testid="stSelectbox"] button, .stApp [data-testid="stMultiSelect"] button:not([class*="Tag"]) { background:transparent !important; border:0 !important; box-shadow:none !important; }
/* toggles & checkboxes: explicit track/thumb colours for every theme combo */
.stApp [data-testid="stCheckbox"] label { background:transparent !important; }
.stApp [data-testid="stCheckbox"] label:has(input[role="switch"]) > div:first-of-type { background:rgba(120,120,128,0.36) !important; border-radius:999px; }
.stApp [data-testid="stCheckbox"] label:has(input[role="switch"]:checked) > div:first-of-type { background:var(--cta) !important; }
.stApp [data-testid="stCheckbox"] label:has(input[role="switch"]) > div:first-of-type > div { background:#fff !important; box-shadow:0 1px 3px rgba(0,0,0,0.3); }
.stApp [data-testid="stCheckbox"] label:has(input:not([role="switch"])) > div:first-of-type { background:var(--fill) !important; border:1.5px solid var(--txt-3) !important; border-radius:6px; }
.stApp [data-testid="stCheckbox"] label:has(input:not([role="switch"]):checked) > div:first-of-type { background:var(--cta) !important; border-color:var(--cta) !important; }
.stApp [data-testid="stCheckbox"] label:has(input:not([role="switch"]):checked) > div:first-of-type svg { fill:#fff !important; color:#fff !important; }
/* multiselect chips on react-aria markup: span[data-tag] (baseweb markup handled above) */
.stApp [data-testid="stMultiSelect"] [role="group"][aria-label="Selected values"] { display:inline-flex !important; flex-wrap:wrap !important; gap:4px; max-width:100%; background:transparent !important; }
.stApp [data-tag] { display:inline-flex !important; align-items:center; gap:2px; width:auto !important; max-width:100%; height:auto !important; min-height:0 !important; margin:0 !important;
    padding:2px 4px 2px 10px !important; border-radius:999px !important; background:var(--accent-soft) !important; background-image:none !important; border:0 !important;
    color:var(--accent) !important; -webkit-text-fill-color:var(--accent) !important; font-size:0.8125rem !important; font-weight:500 !important; line-height:1.5 !important; flex:0 0 auto; }
.stApp [data-tag] * { color:var(--accent) !important; -webkit-text-fill-color:var(--accent) !important; font-size:0.8125rem !important; background:transparent !important; }
.stApp [data-tag] > span { max-width:220px; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
.stApp [data-tag] button { width:18px !important; height:18px !important; min-height:0 !important; padding:0 !important; border:0 !important; border-radius:50% !important; display:inline-flex; align-items:center; justify-content:center; }
.stApp [data-tag] button svg { width:12px !important; height:12px !important; fill:var(--accent) !important; color:var(--accent) !important; }
.stApp input:focus, .stApp input:focus-visible, .stApp textarea:focus, .stApp textarea:focus-visible { outline:none !important; box-shadow:none !important; border:0 !important; }
/* number-input steppers */
.stApp [data-testid="stNumberInputStepDown"], .stApp [data-testid="stNumberInputStepUp"] { background:var(--fill) !important; color:var(--txt) !important; border:0 !important; }
.stApp [data-testid="stNumberInputStepDown"] svg, .stApp [data-testid="stNumberInputStepUp"] svg { fill:var(--txt) !important; color:var(--txt) !important; }
.stApp [data-testid="stNumberInputStepDown"]:hover, .stApp [data-testid="stNumberInputStepUp"]:hover { background:var(--accent-soft) !important; }
/* multiselect: compact rounded chips that wrap INSIDE the control */
.stApp [data-testid="stMultiSelect"] [data-baseweb="select"] > div { flex-wrap:wrap !important; height:auto !important; min-height:44px; padding:4px 8px !important; gap:4px; align-items:center; }
.stApp [data-testid="stMultiSelect"] [data-baseweb="select"] > div > div:first-child { flex-wrap:wrap !important; gap:4px; width:auto; flex:1 1 120px; min-width:0; background:transparent !important; }
.stApp span[data-baseweb="tag"] {
    display:inline-flex !important; align-items:center; width:auto !important; max-width:100%; height:auto !important; min-height:0 !important; margin:2px 4px 2px 0 !important;
    padding:2px 4px 2px 10px !important; border-radius:999px !important; background:var(--accent-soft) !important; background-image:none !important;
    color:var(--accent) !important; font-size:0.8125rem !important; font-weight:500 !important; line-height:1.5 !important; flex:0 0 auto;
}
.stApp span[data-baseweb="tag"], .stApp span[data-baseweb="tag"] *:not(svg):not(path) { color:var(--accent) !important; -webkit-text-fill-color:var(--accent) !important; font-size:0.8125rem !important; background-color:transparent !important; }
.stApp span[data-baseweb="tag"] span[title], .stApp span[data-baseweb="tag"] > span:first-child { max-width:220px; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
.stApp span[data-baseweb="tag"] svg { fill:var(--accent) !important; color:var(--accent) !important; width:12px; height:12px; }
.stApp span[data-baseweb="tag"] [role="presentation"], .stApp span[data-baseweb="tag"] [data-baseweb="icon"] { background:transparent !important; width:auto !important; height:auto !important; }
/* popovers, menus, options (portaled to body — NOT inside .stApp) */
div[data-baseweb="popover"], div[data-baseweb="popover"] > div { background:transparent !important; color:var(--txt) !important; }
div[data-baseweb="popover"] > div > div, div[data-baseweb="popover"] ul, div[data-baseweb="menu"], div[data-baseweb="popover"] [role="listbox"], div[data-baseweb="popover"] [data-baseweb="calendar"] {
    background:var(--card) !important; background-color:var(--card) !important; color:var(--txt) !important; border-radius:var(--r-md) !important;
}
div[data-baseweb="popover"] li, div[data-baseweb="popover"] [role="option"], div[data-baseweb="menu"] li, div[data-baseweb="menu"] [role="option"] { background:transparent !important; color:var(--txt) !important; -webkit-text-fill-color:var(--txt) !important; }
div[data-baseweb="popover"] li *, div[data-baseweb="popover"] [role="option"] *, div[data-baseweb="menu"] li * { color:var(--txt) !important; -webkit-text-fill-color:var(--txt) !important; background:transparent !important; }
div[data-baseweb="popover"] li:hover, div[data-baseweb="popover"] li[aria-selected="true"], div[data-baseweb="popover"] [role="option"]:hover, div[data-baseweb="popover"] [role="option"][aria-selected="true"], div[data-baseweb="popover"] li[data-highlighted="true"] { background:var(--fill) !important; }
div[data-baseweb="popover"] li[aria-disabled="true"], div[data-baseweb="popover"] li[aria-disabled="true"] * { color:var(--txt-2) !important; -webkit-text-fill-color:var(--txt-2) !important; }
div[data-baseweb="popover"] svg { fill:var(--txt-2) !important; }
div[data-baseweb="popover"] input { background:transparent !important; }
div[data-baseweb="tooltip"], div[data-baseweb="tooltip"] > div, [data-testid="stTooltipContent"] { background:var(--card) !important; color:var(--txt) !important; border:1px solid var(--hair); }
div[data-baseweb="tooltip"] *, [data-testid="stTooltipContent"] * { color:var(--txt) !important; }
/* popover surfaces use color-scheme of the ACTIVE app theme */
body:has(#dmchk:checked) div[data-baseweb="popover"] { color-scheme:dark; }
body:not(:has(#dmchk:checked)) div[data-baseweb="popover"] { color-scheme:light; }
/* checkbox / radio / toggle text */
.stApp [data-testid="stCheckbox"] label *, .stApp [data-testid="stToggle"] label *, .stApp [data-testid="stRadio"] label[data-baseweb="radio"] p { -webkit-text-fill-color:currentColor; }
.stApp [data-testid="stCheckbox"] label p, .stApp [data-testid="stToggle"] label p { color:var(--txt) !important; }
.stApp [data-testid="stRadio"] label:has(input:checked) p, .stApp label[data-testid="stRadioOption"][data-selected="true"] p { color:var(--txt) !important; -webkit-text-fill-color:var(--txt) !important; }
/* expanders: header text/icon from tokens */
.stApp [data-testid="stExpander"] summary, .stApp [data-testid="stExpander"] summary *, .stApp [data-testid="stExpander"] summary p { color:var(--txt) !important; -webkit-text-fill-color:var(--txt) !important; }
.stApp [data-testid="stExpander"] summary svg { fill:var(--txt-3) !important; color:var(--txt-3) !important; }
.stApp [data-testid="stExpander"] details, .stApp [data-testid="stExpander"] details > div { color:var(--txt); }
.stApp [data-testid="stFileUploaderDropzone"] { background:var(--fill) !important; color:var(--txt) !important; border:1px dashed var(--hair) !important; border-radius:var(--r-md) !important; }
.stApp [data-testid="stFileUploaderDropzone"] *:not(button):not(button *) { color:var(--txt-2) !important; }
.stApp [data-testid="stAlert"], .stApp [data-testid="stAlert"] * { color:var(--txt) !important; }
.stApp [data-testid="stAlert"] { background:var(--fill) !important; }
.stApp [data-testid="stDataFrame"], .stApp [data-testid="stTable"] { color-scheme:inherit; }
.stApp code { background:var(--fill) !important; color:var(--txt) !important; }
/* buttons — colour from tokens in every theme combination */
.stApp .stButton > button:not([kind="primary"]), .stApp [data-testid="stDownloadButton"] button, .stApp [data-testid="stBaseButton-secondary"] { background:var(--fill) !important; color:var(--accent) !important; border:0 !important; }
.stApp .stButton > button:not([kind="primary"]) *, .stApp [data-testid="stDownloadButton"] button * { color:var(--accent) !important; -webkit-text-fill-color:var(--accent) !important; }
.stApp .stButton > button:disabled, .stApp [data-testid="stDownloadButton"] button:disabled { opacity:0.5 !important; }
.stApp .stButton > button[kind="primary"], .stApp div[class*="st-key-generate_btn"] button { color:#fff !important; }
.stApp .stButton > button[kind="primary"] *, .stApp div[class*="st-key-generate_btn"] button * { color:#fff !important; -webkit-text-fill-color:#fff !important; }
/* COMPACT SECONDARY BUTTONS — the primary-CTA pill rules above must never leak onto ordinary buttons */
.stApp .stButton > button:not([kind="primary"]):not([data-testid="stBaseButton-primary"]) { width:auto; min-width:0; max-width:100%; min-height:40px; padding:0.5rem 1.1rem !important; font-size:0.875rem !important; display:inline-flex; margin:0.15rem 0; }
.stApp div.stButton:not(:has(button[kind="primary"])) { display:block; width:auto; margin:0; justify-content:flex-start; }
.stApp div.stButton > button p { font-size:inherit !important; }

div[class*="st-key-sec_"] button, div[class*="st-key-sec_"] [data-testid="stBaseButton-secondary"] { width:auto !important; min-width:0 !important; }
div[class*="st-key-sec_"] > div, div[class*="st-key-sec_"] .stButton { width:auto !important; }

/* ═══ ROUND 5 — new components (all colours from tokens → correct in every OS × app theme combination) ═══ */
.sr-only { position:absolute !important; width:1px; height:1px; margin:-1px; padding:0; overflow:hidden; clip:rect(0,0,0,0); white-space:nowrap; border:0; }
.hint-card { margin:var(--sp-2) 0; padding:var(--sp-2) var(--sp-3); border-radius:var(--r-md); background:var(--fill); border:1px solid var(--hair); color:var(--txt); font-size:0.9375rem; }
.hint-card .hint-title { font-weight:600; display:flex; gap:8px; align-items:baseline; flex-wrap:wrap; color:var(--txt); }
.hint-card .glyph { font-weight:700; color:var(--accent); }
.hint-card.warn { border-left:4px solid var(--warn); }
.hint-card.warn .glyph { color:var(--warn); }
.hint-card.ok { border-left:4px solid var(--ok); }
.hint-card.ok .glyph { color:var(--ok); }
.hint-card ul { margin:6px 0 0; padding-left:1.2rem; } .hint-card li, .hint-card .hint-body { color:var(--txt-2); margin:3px 0; }
.hint-card .chk-h { margin-top:8px; font-weight:600; color:var(--txt); } .hint-card .chk-sub { font-weight:400; color:var(--txt-2); font-size:0.8125rem; }
.numbers-strip { display:flex; flex-wrap:wrap; align-items:center; gap:8px; margin:0 0 var(--sp-2); padding:10px var(--sp-2); border-radius:var(--r-md); background:var(--fill); }
.numbers-strip .ns-label { font-size:0.75rem; font-weight:700; letter-spacing:0.06em; text-transform:uppercase; color:var(--txt-2); margin-right:4px; }
.numbers-strip .ns-chip { padding:3px 12px; border-radius:999px; background:var(--card); border:1px solid var(--hair); font-size:0.875rem; color:var(--txt); }
.numbers-strip .ns-chip b { color:var(--accent); font-weight:700; }
.goal-card { margin:var(--sp-2) 0; padding:var(--sp-2) var(--sp-3); border-radius:var(--r-md); background:var(--fill); }
.goal-card .goal-text { font-size:1.0625rem; font-weight:600; color:var(--txt); margin:2px 0 10px; }
.goal-bar { height:10px; border-radius:99px; background:var(--card); border:1px solid var(--hair); overflow:hidden; }
.goal-bar i { display:block; height:100%; background:var(--cta); border-radius:99px; }
.goal-card .goal-meta { margin-top:8px; font-size:0.875rem; color:var(--txt-2); } .goal-card .goal-meta b { color:var(--txt); }
.bk-table { width:100%; border-collapse:collapse; margin:8px 0; font-size:0.875rem; color:var(--txt); }
.bk-table th, .bk-table td { text-align:left; padding:6px 10px; border-bottom:1px solid var(--hair); color:var(--txt); } .bk-table th { color:var(--txt-2); font-weight:600; }
.sev-tag { font-weight:700; margin-left:4px; }
/* focus rings (keyboard) — visible on every interactive element */
.stApp button:focus-visible, .stApp a:focus-visible, .stApp [role="tab"]:focus-visible, .stApp summary:focus-visible, .stApp [role="switch"]:focus-visible, .dm-label:focus-visible, .fs-btn:focus-visible { outline:3px solid var(--accent) !important; outline-offset:2px !important; border-radius:8px; }
.stApp [data-testid="stCheckbox"] input:focus-visible + div, .stApp [data-testid="stRadio"] input:focus-visible + div { outline:3px solid var(--accent); outline-offset:2px; }
/* keep new buttons compact (placed AFTER the global CTA rules) */
div[class*="st-key-rev_"] button, div[class*="st-key-aud_"] button, div[class*="st-key-ver_"] button, div[class*="st-key-dl_"] button, div[class*="st-key-prefill_"] button, div[class*="st-key-week_"] button {
    width:auto !important; min-width:0 !important; max-width:300px !important; min-height:40px !important; padding:0.5rem 1.1rem !important; font-size:0.875rem !important; }
div[class*="st-key-rev_"], div[class*="st-key-aud_"], div[class*="st-key-ver_"], div[class*="st-key-dl_"], div[class*="st-key-prefill_"], div[class*="st-key-week_"] { width:auto !important; }
.stApp div.stButton:not(:has(button[kind="primary"])) button, .stApp [data-testid="stDownloadButton"] button { max-width:min(100%,300px) !important; }
.stApp .stButton > button:not([kind="primary"]) p, .stApp [data-testid="stDownloadButton"] button p { white-space:normal; line-height:1.25; }
.stApp [data-testid="stElementContainer"]:has(#sangha-hc), .stApp div.element-container:has(#sangha-hc) { display:none; }
body:has(#dmchk:checked) { --warn:#ffb74d; --ok:#6fdc94; --bad:#ff6b6b; }
/* HIGH CONTRAST — manual toggle (marker element) and the OS "prefers-contrast: more" setting */
body:has(#sangha-hc):not(:has(#dmchk:checked)) { --txt:#000; --txt-2:#1a1a1a; --txt-3:#262626; --hair:rgba(0,0,0,0.55); --hair-2:rgba(0,0,0,0.35); --accent:#7a2509; --cta:#8a2d0e; --cta-2:#74240a; --fill:#e6e6ea; --sev2:#6b2f00; --warn:#7a3d00; --ok:#0e5a24; }
body:has(#sangha-hc):has(#dmchk:checked) { --txt:#fff; --txt-2:#f2f2f2; --txt-3:#e6e6e6; --hair:rgba(255,255,255,0.7); --hair-2:rgba(255,255,255,0.45); --accent:#ffbfa3; --cta:#c8511f; --fill:#38383a; --sev2:#ffd166; --warn:#ffb74d; --ok:#7ee2a0; }
@media (prefers-contrast: more) {
    body:not(:has(#dmchk:checked)) { --txt:#000; --txt-2:#1a1a1a; --txt-3:#262626; --hair:rgba(0,0,0,0.55); --accent:#7a2509; --cta:#8a2d0e; }
    body:has(#dmchk:checked) { --txt:#fff; --txt-2:#f2f2f2; --txt-3:#e6e6e6; --hair:rgba(255,255,255,0.7); --accent:#ffbfa3; }
}
@media (forced-colors: active) { .stApp button:focus-visible, .stApp [role="tab"]:focus-visible { outline:3px solid Highlight !important; } }
#sangha-toast { position:fixed; right:16px; bottom:16px; z-index:999999; max-width:min(92vw,360px); padding:12px 16px; border-radius:14px; background:var(--card); color:var(--txt); border:1px solid var(--hair); box-shadow:0 12px 32px rgba(0,0,0,0.3); font-size:0.9rem; line-height:1.5; display:none; }
#sangha-toast kbd { padding:1px 6px; border-radius:6px; border:1px solid var(--hair); background:var(--fill); font:600 0.8rem var(--mono); color:var(--txt); }
</style>
"""


def _notify_next_run(msg: str, icon=None) -> None:
    """Queue a confirmation to show on the NEXT run — use right before st.rerun(), since
    anything rendered in the run that calls st.rerun() is discarded before the user sees it."""
    st.session_state["_flash_notice"] = (msg, icon)


def _notify(msg: str, icon=None) -> None:
    """Success confirmation: st.toast where available (>=1.27), else st.success."""
    if hasattr(st, "toast"):
        try:
            st.toast(msg, icon=icon)
            return
        except Exception:
            pass
    st.success(msg)


import contextlib as _ctxlib


@_ctxlib.contextmanager
def _sub_expander(label, expanded=False):
    """Expander that may sit inside another expander. Older Streamlit (<~1.46)
    raises on nested expanders, so fall back to a labelled plain container."""
    try:
        _ex = st.expander(label, expanded=expanded)
    except Exception:
        _ex = None
    if _ex is None:
        st.markdown(f"**{label}**")
        with st.container():
            yield
    else:
        with _ex:
            yield


def _st_version_tuple():
    try:
        return tuple(int(x) for x in st.__version__.split(".")[:2])
    except Exception:
        return (0, 0)


def _dl_button(*args, **kwargs):
    """st.download_button that does NOT rerun the script where supported (Streamlit >=1.43,
    on_click="ignore"); older versions rerun on click, which clears the generated output
    panel (it only renders in the run that generated it). Version-gated: on older releases
    on_click is accepted as a callback and a string would fail at click time."""
    if _st_version_tuple() >= (1, 43):
        kwargs["on_click"] = "ignore"
    return st.download_button(*args, **kwargs)


_flash = st.session_state.pop("_flash_notice", None)
if _flash:
    _notify(_flash[0], _flash[1])


def _plain_label(k: str) -> str:
    """Display-only: drop a leading emoji token from an option key. The underlying
    option value (used as history data / session state) is unchanged."""
    parts = str(k).split(" ", 1)
    return parts[1] if len(parts) == 2 and not parts[0][:1].isalnum() else str(k)


TEAM_SLUG = _slugify_team(st.session_state.team_name)
_TEAM_SUFFIX = "" if TEAM_SLUG == "default" else f"_{TEAM_SLUG}"

# ═══════════════════════════════════════════════════
# SESSION STATE
# ═══════════════════════════════════════════════════
import sqlite3

MAX_HISTORY  = 10
def _sev_tag(days: int) -> str:
    return "\u2716 Critical" if days >= 4 else ("\u25b2 Urgent" if days == 3 else "\u25b2 Watch")


_HEALTH_GLYPH = {"Healthy": "\u2713", "Okay": "\u25cf", "Strained": "\u25b2", "At risk": "\u2716"}   # status is never colour-only
HISTORY_FILE = f".sanghastatus_history{_TEAM_SUFFIX}.json"   # legacy file — auto-migrated into the DB below, then unused
DB_FILE      = f".sanghastatus{_TEAM_SUFFIX}.db"


def _get_db_conn():
    conn = sqlite3.connect(DB_FILE)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT, project TEXT, members INTEGER, tasks INTEGER,
            tone TEXT, domain TEXT, lang TEXT,
            data_json TEXT, members_detail_json TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    # saved_at (a real ISO timestamp, distinct from the human "date" field
    # and from created_at) — added for the standup-cadence reminder. A
    # try/except ALTER keeps this safe against a pre-existing DB file that
    # was created before this column existed.
    try:
        conn.execute("ALTER TABLE history ADD COLUMN saved_at TEXT")
    except sqlite3.OperationalError:
        pass
    return conn


# ── GENERIC KEY-VALUE TABLES — used to migrate roster/presets/glossary/
# settings off flat JSON files and into the SAME SQLite DB as history,
# keyed by team slug so each team's data stays isolated exactly like the
# per-team JSON files did. One tiny table per feature (not one shared
# table) so each stays independently inspectable, but all three share
# this same get/set helper pair since the shape (one JSON blob per team)
# is identical. Table names here are fixed, code-controlled strings
# (never user input), so the f-string is safe from injection. ──
def _kv_get_raw(table: str, team_slug: str):
    conn = _get_db_conn()
    conn.execute(f"CREATE TABLE IF NOT EXISTS {table} (team_slug TEXT PRIMARY KEY, value_json TEXT)")
    row = conn.execute(f"SELECT value_json FROM {table} WHERE team_slug=?", (team_slug,)).fetchone()
    conn.close()
    return row[0] if row else None


def _kv_set_raw(table: str, team_slug: str, value) -> None:
    conn = _get_db_conn()
    conn.execute(f"CREATE TABLE IF NOT EXISTS {table} (team_slug TEXT PRIMARY KEY, value_json TEXT)")
    conn.execute(
        f"INSERT INTO {table} (team_slug, value_json) VALUES (?,?) "
        f"ON CONFLICT(team_slug) DO UPDATE SET value_json=excluded.value_json",
        (team_slug, json.dumps(value))
    )
    conn.commit()
    conn.close()


def _kv_load_with_json_migration(table: str, team_slug: str, json_file: str, default):
    """Shared load pattern for roster/presets/glossary: DB row wins if
    present; otherwise, a one-time best-effort migration from the legacy
    per-team JSON file (if it exists) seeds the DB row so this only
    happens once. Never crashes — falls back to `default` (a fresh start
    for that team) on any error, exactly like the old JSON loaders did."""
    try:
        raw = _kv_get_raw(table, team_slug)
        if raw is not None:
            return json.loads(raw)
    except Exception:
        pass
    try:
        if os.path.exists(json_file):
            with open(json_file, "r") as f:
                legacy = json.load(f)
            try:
                _kv_set_raw(table, team_slug, legacy)
            except Exception:
                pass  # migration write failed — still hand back the legacy data this run
            return legacy
    except Exception:
        pass
    return default



# ═══════════════════════════════════════════════════
# UI PREFS + UI-LANGUAGE (item 41). Persisted per team in the same SQLite DB (table
# "ui_prefs", one JSON blob per team slug — same helper pattern as roster/presets).
# T("key") returns the string in the chosen UI language and falls back to English.
# Generated-OUTPUT language is a separate, pre-existing setting (pref_lang).
# ═══════════════════════════════════════════════════
_UI_PREF_KEYS = ("pref_ui_lang", "pref_contrast", "pref_template", "pref_brand_project")
UI_LANG_OPTIONS = {"English": "en", "हिन्दी": "hi", "मराठी": "mr"}


def _load_ui_prefs() -> dict:
    try:
        raw = _kv_get_raw("ui_prefs", TEAM_SLUG)
        return json.loads(raw) if raw else {}
    except Exception:
        return {}


def _save_ui_prefs() -> None:
    try:
        _kv_set_raw("ui_prefs", TEAM_SLUG, {k: st.session_state.get(k) for k in _UI_PREF_KEYS})
    except Exception:
        pass


_UI_LOADED_FLAG = f"_ui_prefs_loaded_{TEAM_SLUG}"
if not st.session_state.get(_UI_LOADED_FLAG):
    _p = _load_ui_prefs()
    for _k in _UI_PREF_KEYS:
        if _k in _p and _p[_k] is not None:
            st.session_state[_k] = _p[_k]
    st.session_state[_UI_LOADED_FLAG] = True
st.session_state.setdefault("pref_ui_lang", "English")
st.session_state.setdefault("pref_contrast", False)
st.session_state.setdefault("pref_template", "Standup")
st.session_state.setdefault("pref_brand_project", "")

_I18N = {
    "en": {
        "hero_eyebrow": "Team standups, simplified",
        "hero_sub": "Turn raw team notes into polished updates — narrative, chat, WhatsApp and email — in seconds.",
        "hero_meaning": "Sangha · the Pali word for “community” · focusing on the team",
        "customize": "Customize — tone, language, team, presets & more",
        "tab_style": "Style", "tab_team": "Team", "tab_presets": "Presets", "tab_glossary": "Glossary",
        "tab_backup": "Backup", "tab_sprint": "Sprint", "tab_brand": "Brand",
        "step1": "Step 1", "step1_title": "Paste your team’s updates",
        "step1_sub": "Raw notes work fine — for engineering, functional or HR teams. Names are detected automatically.",
        "step2": "Step 2", "step2_title": "Your team at a glance",
        "members": "Members", "tasks": "Tasks", "blockers": "Blockers",
        "standup_date": "Standup date", "tone": "Tone", "domain": "Domain", "out_lang": "Output language",
        "project_tag": "Project / sprint tag", "incl_tomorrow": "Include tomorrow's plan", "hl_blockers": "Highlight blockers",
        "template": "Template", "ui_lang": "Interface language", "high_contrast": "High contrast",
        "generate": "Generate Professional Status", "prefill": "Prefill from yesterday",
        "clear_output": "Clear output", "refine": "Refine this update",
        "history": "History", "past_standups": "Past standups", "sprint_goal": "Sprint goal",
        "whos_out": "Who’s out today?", "empty_title": "Paste your team’s updates to get started",
        "shortcuts": "Keyboard shortcuts", "reset": "Reset preferences",
    },
    "hi": {
        "hero_eyebrow": "टीम स्टैंडअप, आसान तरीके से",
        "hero_sub": "टीम के कच्चे नोट्स को सेकंडों में साफ़-सुथरे अपडेट में बदलें — विवरण, चैट, WhatsApp और ईमेल।",
        "hero_meaning": "संघ · पाली शब्द जिसका अर्थ “समुदाय” है · टीम पर ध्यान",
        "customize": "अनुकूलित करें — टोन, भाषा, टीम, प्रीसेट और बहुत कुछ",
        "tab_style": "शैली", "tab_team": "टीम", "tab_presets": "प्रीसेट", "tab_glossary": "शब्दकोश",
        "tab_backup": "बैकअप", "tab_sprint": "स्प्रिंट", "tab_brand": "ब्रांड",
        "step1": "चरण 1", "step1_title": "अपनी टीम के अपडेट पेस्ट करें",
        "step1_sub": "कच्चे नोट्स भी चलेंगे — इंजीनियरिंग, फ़ंक्शनल या HR टीम के लिए। नाम अपने-आप पहचाने जाते हैं।",
        "step2": "चरण 2", "step2_title": "आपकी टीम एक नज़र में",
        "members": "सदस्य", "tasks": "कार्य", "blockers": "रुकावटें",
        "standup_date": "स्टैंडअप की तारीख", "tone": "टोन", "domain": "क्षेत्र", "out_lang": "आउटपुट की भाषा",
        "project_tag": "प्रोजेक्ट / स्प्रिंट टैग", "incl_tomorrow": "कल की योजना शामिल करें", "hl_blockers": "रुकावटें हाइलाइट करें",
        "template": "टेम्पलेट", "ui_lang": "इंटरफ़ेस की भाषा", "high_contrast": "उच्च कंट्रास्ट",
        "generate": "प्रोफ़ेशनल स्टेटस बनाएँ", "prefill": "कल से पहले से भरें",
        "clear_output": "आउटपुट साफ़ करें", "refine": "इस अपडेट को सुधारें",
        "history": "इतिहास", "past_standups": "पिछले स्टैंडअप", "sprint_goal": "स्प्रिंट लक्ष्य",
        "whos_out": "आज कौन छुट्टी पर है?", "empty_title": "शुरू करने के लिए अपनी टीम के अपडेट पेस्ट करें",
        "shortcuts": "कीबोर्ड शॉर्टकट", "reset": "प्राथमिकताएँ रीसेट करें",
    },
    "mr": {
        "hero_eyebrow": "टीम स्टँडअप, सोप्या पद्धतीने",
        "hero_sub": "टीमच्या कच्च्या नोट्सचे काही सेकंदांत नीटनेटक्या अपडेटमध्ये रूपांतर करा — वर्णन, चॅट, WhatsApp आणि ईमेल.",
        "hero_meaning": "संघ · पाली शब्द ज्याचा अर्थ “समुदाय” · टीमवर लक्ष केंद्रित",
        "customize": "सानुकूल करा — टोन, भाषा, टीम, प्रीसेट आणि बरेच काही",
        "tab_style": "शैली", "tab_team": "टीम", "tab_presets": "प्रीसेट", "tab_glossary": "शब्दकोश",
        "tab_backup": "बॅकअप", "tab_sprint": "स्प्रिंट", "tab_brand": "ब्रँड",
        "step1": "पायरी 1", "step1_title": "तुमच्या टीमचे अपडेट पेस्ट करा",
        "step1_sub": "कच्च्या नोट्सही चालतील — इंजिनिअरिंग, फंक्शनल किंवा HR टीमसाठी. नावे आपोआप ओळखली जातात.",
        "step2": "पायरी 2", "step2_title": "तुमची टीम एका दृष्टिक्षेपात",
        "members": "सदस्य", "tasks": "कामे", "blockers": "अडथळे",
        "standup_date": "स्टँडअपची तारीख", "tone": "टोन", "domain": "क्षेत्र", "out_lang": "आउटपुटची भाषा",
        "project_tag": "प्रोजेक्ट / स्प्रिंट टॅग", "incl_tomorrow": "उद्याची योजना समाविष्ट करा", "hl_blockers": "अडथळे हायलाइट करा",
        "template": "टेम्पलेट", "ui_lang": "इंटरफेसची भाषा", "high_contrast": "उच्च कॉन्ट्रास्ट",
        "generate": "प्रोफेशनल स्टेटस तयार करा", "prefill": "कालच्यावरून आधी भरा",
        "clear_output": "आउटपुट काढा", "refine": "हे अपडेट सुधारा",
        "history": "इतिहास", "past_standups": "मागील स्टँडअप", "sprint_goal": "स्प्रिंट उद्दिष्ट",
        "whos_out": "आज कोण रजेवर आहे?", "empty_title": "सुरू करण्यासाठी तुमच्या टीमचे अपडेट पेस्ट करा",
        "shortcuts": "कीबोर्ड शॉर्टकट", "reset": "प्राधान्ये रीसेट करा",
    },
}


def T(key: str) -> str:
    """UI string in the chosen interface language; falls back to English, then to the key."""
    code = UI_LANG_OPTIONS.get(st.session_state.get("pref_ui_lang", "English"), "en")
    return _I18N.get(code, {}).get(key) or _I18N["en"].get(key) or key


# 43: strip comments + indentation from the CSS before sending (smaller payload, fewer style bytes to parse)
_CSS_MIN = re.sub(r'\n\s+', '\n', re.sub(r'/\*.*?\*/', '', CSS, flags=re.S))
st.markdown(_CSS_MIN, unsafe_allow_html=True)
if st.session_state.get("pref_contrast"):
    st.markdown('<span id="sangha-hc" hidden></span>', unsafe_allow_html=True)   # 40: high-contrast marker (CSS keys off it)
# Hidden state inputs (static markup so they survive team-name changes).
st.markdown(
    '<input type="checkbox" id="dmchk" aria-label="Toggle dark mode">'
    '<input type="radio" name="fontsize" id="fsSmall">'
    '<input type="radio" name="fontsize" id="fsNormal" checked>'
    '<input type="radio" name="fontsize" id="fsLarge">',
    unsafe_allow_html=True
)
st.markdown(
    '<div class="topbar"><div class="topbar-in">'
    '<div class="tb-brand"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" '
    'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M3 21h18M5 21V10M10 21V10M14 21V10M19 21V10M2 10l10-6 10 6z"/></svg>'
    'SanghaStatus</div>'
    f'<div class="tb-team" title="Current team">{_html.escape(st.session_state.team_name or "default")}</div>'
    '<div class="tb-spacer"></div>'
    '<div class="fs-toggle"><label for="fsSmall" class="fs-btn" aria-label="Smaller text">A-</label>'
    '<label for="fsNormal" class="fs-btn" aria-label="Normal text">A</label>'
    '<label for="fsLarge" class="fs-btn" aria-label="Larger text">A+</label></div>'
    '<label for="dmchk" class="dm-label" role="switch" aria-label="Dark mode switch" tabindex="0" '
    'onkeydown="if(event.key===\'Enter\'||event.key===\' \'){event.preventDefault();document.getElementById(\'dmchk\').click();}"></label>'
    '</div></div>',
    unsafe_allow_html=True
)

# ═══════════════════════════════════════════════════
# HERO
# ═══════════════════════════════════════════════════
st.markdown(
    '<div class="hero-section">'
    '<div class="hero-glow"></div>'
    f'<div class="eyebrow">{_html.escape(T("hero_eyebrow"))}</div>'
    '<div class="main-title" role="heading" aria-level="1">Sangha<span class="accent-grad">Status</span></div>'
    f'<div class="main-subtitle">{_html.escape(T("hero_sub"))}</div>'
    f'<div class="sangha-meaning">{_html.escape(T("hero_meaning"))}</div>'
    '</div>',
    unsafe_allow_html=True
)


def _render_team_switch():
    """Team switch/create row. Rendered inside Customize > Team normally, or at
    top level when the current team is PIN-locked (so the person can always
    switch away)."""
    _tm_col1, _tm_col2 = st.columns([4, 1])
    with _tm_col1:
        # Seed the widget's own state ONCE; passing value= alongside key= (while state also moves) is what
        # made inputs show their default concatenated repeatedly.
        if "team_name_widget" not in st.session_state:
            st.session_state["team_name_widget"] = st.session_state.team_name
        _team_name_input = st.text_input(
            "Team name", key="team_name_widget", placeholder="default",
            help="Switch or create a team \u2014 each team keeps its own roster, history & glossary."
        )
    with _tm_col2:
        st.write("")
        if st.button("Switch", key="sec_switch_team_btn", use_container_width=True):
            st.session_state.team_name = _team_name_input.strip() or "default"
            _save_last_team(st.session_state.team_name)
            st.rerun()


# ═══════════════════════════════════════════════════
# PER-TEAM PIN — optional lightweight access gate. A team with no PIN ever
# set (including "default", unless someone deliberately sets one) behaves
# exactly as before — nobody is forced to add a PIN. The PIN itself is
# never stored in plain text, only a stdlib sha256 hash of it, in the same
# SQLite DB (a new "team_pin" table, keyed by team slug) as everything
# else migrated in item 4 above. ──
def _get_team_pin_hash():
    try:
        raw = _kv_get_raw("team_pin", TEAM_SLUG)
        return json.loads(raw).get("pin_hash") if raw else None
    except Exception:
        return None


def _set_team_pin_hash(pin_hash) -> None:
    try:
        _kv_set_raw("team_pin", TEAM_SLUG, {"pin_hash": pin_hash})
    except Exception:
        pass


_PIN_OK_KEY = f"pin_verified_{TEAM_SLUG}"
_team_pin_hash = _get_team_pin_hash()

if _team_pin_hash and not st.session_state.get(_PIN_OK_KEY):
    st.session_state.pop("last_output", None)
    st.warning(f"🔒 Team **{st.session_state.team_name}** is PIN-protected.")
    _pin_attempt = st.text_input("Enter team PIN", type="password", key="pin_attempt_input")
    if st.button("Unlock", key="sec_pin_unlock_btn"):
        if hashlib.sha256(_pin_attempt.encode()).hexdigest() == _team_pin_hash:
            st.session_state[_PIN_OK_KEY] = True
            st.rerun()
        else:
            st.error("Incorrect PIN.")
    st.markdown('<div class="eyebrow" style="margin-top:2rem;">Or switch team</div>', unsafe_allow_html=True)
    _render_team_switch()
    st.stop()

# ═══════════════════════════════════════════════════
# CUSTOMIZE — every secondary control lives here so the main screen stays
# hero -> updates -> Generate. NOTE: this is an expander (always rendered), not
# st.dialog: widgets inside a dialog are only rendered while it is open, so
# Streamlit would drop their session_state (pref_*, glossary/preset inputs) and
# break generation + persistence when it closes.
# ═══════════════════════════════════════════════════
_cz = st.expander(T("customize"), expanded=False)
with _cz:
    _cz_tabs = st.tabs([T("tab_style"), T("tab_team"), T("tab_presets"), T("tab_glossary"), T("tab_backup"), T("tab_sprint"), T("tab_brand")])
with _cz_tabs[1]:
    st.markdown('<div class="eyebrow">Team</div>', unsafe_allow_html=True)
    _render_team_switch()

with _cz_tabs[1]:
    st.markdown('<div class="eyebrow" style="margin-top:1.5rem;">Team PIN \u00b7 optional</div>', unsafe_allow_html=True)
    st.caption(
        "Optional. Only a sha256 hash of the PIN is stored, scoped to this team. "
        "Leave this alone and nothing changes — 'default' and every other team stay open unless a PIN is set here."
    )
    _pin_col1, _pin_col2 = st.columns([2, 1])
    with _pin_col1:
        _new_pin = st.text_input(
            "Set / change PIN for this team", type="password", key="new_team_pin_input",
            placeholder="4+ characters"
        )
    with _pin_col2:
        st.write("")
        if st.button("Save PIN", key="sec_save_team_pin_btn", use_container_width=True):
            if len(_new_pin) < 4:
                st.warning("Use at least 4 characters.")
            else:
                _set_team_pin_hash(hashlib.sha256(_new_pin.encode()).hexdigest())
                st.session_state[_PIN_OK_KEY] = True
                _notify_next_run("PIN saved for this team")
                st.rerun()
    if _team_pin_hash and st.button("🗑️ Remove PIN for this team", key="sec_remove_team_pin_btn"):
        _set_team_pin_hash(None)
        _notify_next_run("PIN removed \u2014 this team is open again.")
        st.rerun()

# ═══════════════════════════════════════════════════
# UNIFIED SETTINGS — shared with SatiCast
# ═══════════════════════════════════════════════════
# Same shared-settings file SatiCast writes to (see its own comment for the
# full caveat): only actually shared across apps on the same filesystem —
# otherwise this quietly falls back to "remembers your name in this app only".
SHARED_SETTINGS_FILE = ".sati_sangha_shared_settings.json"


def load_shared_settings() -> dict:
    try:
        if os.path.exists(SHARED_SETTINGS_FILE):
            with open(SHARED_SETTINGS_FILE, "r") as f:
                return json.load(f)
    except Exception:
        pass
    return {}


def save_shared_settings(updates: dict) -> None:
    try:
        current = load_shared_settings()
        current.update(updates)
        with open(SHARED_SETTINGS_FILE, "w") as f:
            json.dump(current, f)
    except Exception:
        pass


ROSTER_FILE = f".sanghastatus_roster{_TEAM_SUFFIX}.json"


def load_roster() -> dict:
    """Persisted team-member profile memory: {name_lower: {"display": str,
    "role": str}}. Same shared-file caveat as history/settings — survives
    refreshes on this deployment, not a per-user database. Backed by the
    SQLite DB's "roster" table now (see _kv_load_with_json_migration);
    ROSTER_FILE is only read once, as a legacy fallback."""
    return _kv_load_with_json_migration("roster", TEAM_SLUG, ROSTER_FILE, {})


def save_roster(roster: dict) -> None:
    try:
        _kv_set_raw("roster", TEAM_SLUG, roster)
    except Exception:
        pass


def load_history_from_disk() -> list:
    """
    Persistence across page refreshes within the SAME running deployment,
    now backed by a real SQLite database (.sanghastatus.db) instead of a
    flat JSON file — proper indexing/querying, and it transparently
    migrates any pre-existing JSON history file into the DB the first time
    it runs. IMPORTANT CAVEAT (unchanged from the JSON version): this is
    still a single database FILE on the server's local disk, so it is:
      - SHARED across every visitor to this deployment (not private per user)
      - LOST on a fresh redeploy or if the platform's filesystem is ephemeral
    True per-user persistence would need a real client-server database with
    user accounts. This is appropriate for a small private/team deployment,
    not a public multi-tenant one.
    """
    try:
        conn = _get_db_conn()
        # One-time migration from the legacy JSON file, only if the DB is
        # still empty — never overwrites DB rows that already exist.
        if conn.execute("SELECT COUNT(*) FROM history").fetchone()[0] == 0 and os.path.exists(HISTORY_FILE):
            try:
                with open(HISTORY_FILE, "r") as f:
                    old_entries = json.load(f)
                for e in reversed(old_entries):  # oldest first, so id order matches recency
                    conn.execute(
                        "INSERT INTO history (date, project, members, tasks, tone, domain, lang, data_json, members_detail_json, saved_at) "
                        "VALUES (?,?,?,?,?,?,?,?,?,?)",
                        (e.get("date"), e.get("project"), e.get("members"), e.get("tasks"),
                         e.get("tone"), e.get("domain"), e.get("lang"),
                         json.dumps(e.get("data", {})), json.dumps(e.get("members_detail", [])),
                         e.get("saved_at"))
                    )
                conn.commit()
            except Exception:
                pass
        rows = conn.execute(
            "SELECT date, project, members, tasks, tone, domain, lang, data_json, members_detail_json, saved_at "
            "FROM history ORDER BY id DESC LIMIT ?", (MAX_HISTORY,)
        ).fetchall()
        conn.close()
        return [
            {
                "date": r[0], "project": r[1], "members": r[2], "tasks": r[3],
                "tone": r[4], "domain": r[5], "lang": r[6],
                "data": json.loads(r[7] or "{}"), "members_detail": json.loads(r[8] or "[]"),
                "saved_at": r[9],
            }
            for r in rows
        ]
    except Exception:
        return []


def save_history_to_disk(history: list) -> None:
    """Replaces the table contents with the current in-memory list — keeps
    this a drop-in replacement for the old 'dump the whole list' JSON
    writer so no call site elsewhere in the app needs to change."""
    try:
        conn = _get_db_conn()
        conn.execute("DELETE FROM history")
        for e in reversed(history):  # reversed so autoincrement id order matches recency
            conn.execute(
                "INSERT INTO history (date, project, members, tasks, tone, domain, lang, data_json, members_detail_json, saved_at) "
                "VALUES (?,?,?,?,?,?,?,?,?,?)",
                (e.get("date"), e.get("project"), e.get("members"), e.get("tasks"),
                 e.get("tone"), e.get("domain"), e.get("lang"),
                 json.dumps(e.get("data", {})), json.dumps(e.get("members_detail", [])),
                 e.get("saved_at"))
            )
        conn.commit()
        conn.close()
    except Exception:
        pass  # read-only filesystem or other issue — fail silently, session-state still works


def init_state():
    defaults = {
        "history":        load_history_from_disk(),
        "session_tokens": 0,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_state()

# ═══════════════════════════════════════════════════
# API
# ═══════════════════════════════════════════════════
if "NVIDIA_API_KEY" not in st.secrets:
    st.error("🔑 NVIDIA_API_KEY not found in Streamlit secrets.")
    st.stop()

client = OpenAI(
    base_url="https://integrate.api.nvidia.com/v1",
    api_key=st.secrets["NVIDIA_API_KEY"]
)

# Optional: GitHub activity auto-pull. Only enabled when the deployer has
# added their own credentials to Streamlit secrets — same opt-in pattern
# as the weather/news API keys, so this stays fully invisible until
# someone deliberately configures it. Requires a GitHub personal access
# token (repo/read:user scope is enough) since the public API alone rate-
# limits unauthenticated requests too aggressively for daily use.
GITHUB_TOKEN    = st.secrets.get("GITHUB_TOKEN", "")
GITHUB_USERNAME = st.secrets.get("GITHUB_USERNAME", "")
GITHUB_PULL_ENABLED = bool(GITHUB_TOKEN and GITHUB_USERNAME)


def fetch_github_activity(since_hours: int = 24) -> list:
    """Best-effort pull of the configured user's recent commits across
    their repos, formatted as ready-to-paste bullet lines. Returns [] on
    any failure or if not configured — this is a convenience, never a
    hard dependency."""
    if not GITHUB_PULL_ENABLED:
        return []
    import requests as _requests
    from datetime import timedelta as _timedelta
    try:
        since_iso = (datetime.utcnow() - _timedelta(hours=since_hours)).isoformat() + "Z"
        headers = {"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github+json"}
        events_url = f"https://api.github.com/users/{GITHUB_USERNAME}/events?per_page=30"
        r = _requests.get(events_url, headers=headers, timeout=8)
        if r.status_code != 200:
            return []
        bullets = []
        for ev in r.json():
            if ev.get("created_at", "") < since_iso:
                continue
            if ev.get("type") == "PushEvent":
                repo = ev.get("repo", {}).get("name", "")
                for c in ev.get("payload", {}).get("commits", [])[:3]:
                    msg = (c.get("message") or "").splitlines()[0][:100]
                    if msg:
                        bullets.append(f"- {msg} ({repo})")
            elif ev.get("type") == "PullRequestEvent":
                action = ev.get("payload", {}).get("action", "")
                pr = ev.get("payload", {}).get("pull_request", {})
                title = (pr.get("title") or "")[:100]
                if title:
                    line = f"- {action.capitalize()} PR: {title}"
                    body = (pr.get("body") or "").strip().splitlines()
                    body_line = next((b.strip() for b in body if b.strip()), "")
                    if body_line:
                        line += f" — {body_line[:100]}"
                    bullets.append(line)
            elif ev.get("type") == "PullRequestReviewEvent":
                pr = ev.get("payload", {}).get("pull_request", {})
                state = ev.get("payload", {}).get("review", {}).get("state", "").replace("_", " ")
                title = (pr.get("title") or "")[:80]
                if title and state:
                    bullets.append(f"- Reviewed PR ({state}): {title}")
            elif ev.get("type") == "IssuesEvent":
                action = ev.get("payload", {}).get("action", "")
                issue = ev.get("payload", {}).get("issue", {})
                title = (issue.get("title") or "")[:100]
                if title and action in ("opened", "closed"):
                    bullets.append(f"- {action.capitalize()} issue: {title}")
        return bullets[:12]
    except Exception:
        return []

# ═══════════════════════════════════════════════════
# CONSTANTS
# ═══════════════════════════════════════════════════
TONE_OPTIONS = {
    "📝 Formal":      "Use formal, complete sentences with professional vocabulary.",
    "💬 Semi-formal": "Use clear, professional but conversational sentences.",
    "⚡ Concise":     "Use short, punchy one-line bullets. Be brief and direct.",
}
DOMAIN_OPTIONS = {
    "💻 Software Dev":        "software development",
    "🧪 QA / Testing":        "quality assurance and testing",
    "🚀 DevOps":              "DevOps and infrastructure",
    "🎨 Design / UX":         "UI/UX design",
    "📦 Product":             "product management",
    "💰 Finance":             "financial operations",
    "🧩 Functional Team":     "functional / business operations (process coordination, stakeholder requirements, cross-functional workflows, and operational execution)",
    "🧑‍🤝‍🧑 Human Resource Team": "Human Resources (recruitment, onboarding, employee relations, policy compliance, performance management, and engagement initiatives)",
}
OUTPUT_LANG_OPTIONS = {
    "🇬🇧 English": "English",
    "🇮🇳 हिन्दी":  "Hindi (Devanagari script)",
    "🇮🇳 मराठी":   "Marathi (Devanagari script)",
}

LOADER_STAGES = [
    ("🏛️", "Gathering the Sangha…",             "Assembling your team's raw updates"),
    ("✍️", "Rewriting into professional prose…", "Expanding notes into full sentences"),
    ("✨", "Finalising your update…",             "Running final quality check"),
]

# Short flavor lines that rotate under the main loader stage, pure CSS —
# see SatiCast's identical mechanism for the full explanation.
LOADER_MICRO_COPY = [
    "Untangling bullet points…",
    "Finding each person's throughline…",
    "Smoothing the rough edges…",
    "Checking nobody got lost…",
]

# ═══════════════════════════════════════════════════
# HELPERS
# ═══════════════════════════════════════════════════
def parse_members(raw: str) -> list:
    members = []
    blocks = re.split(r'\n(?=[A-Z][^\n:]{0,30}:)', raw.strip())
    for block in blocks:
        lines = block.strip().splitlines()
        if not lines:
            continue
        header = lines[0].strip().rstrip(":")
        tasks = [l.strip().lstrip("-•*").strip() for l in lines[1:]
                 if l.strip() and l.strip()[0] in "-•*"]
        # Instant, pre-API heuristic for the member-chip badge — deliberately
        # conservative (phrases, not bare words) to avoid flagging normal
        # work like "resolved the issue" or "fixed the bug" as a blocker.
        # The LLM-generated blocker_summary (build_narrative_prompt) does the
        # real semantic judgment call; this is just a cheap instant hint.
        blocker_phrases = [
            "blocked", "block on", "blocked by", "stuck on", "stuck with",
            "waiting on", "waiting for", "pending approval", "pending access",
            "need approval", "need access", "unable to", "not able to",
            "can't proceed", "cannot proceed", "dependency on", "depends on",
        ]
        blockers = [t for t in tasks if any(p in t.lower() for p in blocker_phrases)]
        if header and tasks:
            members.append({"name": header, "tasks": tasks, "blockers": blockers, "count": len(tasks)})
    return members


# ── SLACK/TEAMS THREAD-PASTE PREPROCESSING ──
# A pasted chat-export thread looks like repeated "[Name] HH:MM" or
# "Name  10:32 AM" header lines interleaved with message text, NOT the
# "Name:" + "-" bullet format parse_members() expects. This heuristic
# detects that shape and rewrites it into the "Name:\n- line\n- line"
# shape BEFORE parse_members() runs, so thread pastes still split
# correctly into per-person blocks instead of one unparseable blob.
THREAD_HEADER_RE = re.compile(
    r'^\s*(?:\[(?P<name1>[A-Za-z][\w .]{0,30})\]\s*(?P<time1>\d{1,2}:\d{2}(?:\s?[AaPp][Mm])?)'
    r'|(?P<name2>[A-Za-z][\w .]{0,30})\s{1,4}(?P<time2>\d{1,2}:\d{2}(?:\s?[AaPp][Mm])?))\s*:?\s*$'
    r'|^\s*(?P<name3>[A-Za-z][\w .]{0,30}):\s*(?P<time3>\d{1,2}:\d{2}(?:\s?[AaPp][Mm])?)\s*$'
)


def looks_like_chat_thread(raw: str) -> bool:
    """True when at least 2 lines look like a chat-thread header
    ('[Name] HH:MM' / 'Name HH:MM' / 'Name: HH:MM'), a strong signal this
    is an exported chat paste rather than the plain 'Name:' + bullets
    format — kept conservative so ordinary pastes are never misdetected."""
    lines = [l for l in raw.splitlines() if l.strip()]
    hits = sum(1 for l in lines if THREAD_HEADER_RE.match(l))
    return hits >= 2


def preprocess_chat_thread_paste(raw: str) -> str:
    """Rewrites a detected chat-thread export into the 'Name:\\n- msg'
    shape parse_members() already understands, merging consecutive
    message lines under the most recent header into '-' bullets. A
    no-op (returns raw unchanged) when looks_like_chat_thread() is False,
    so ordinary pastes are never touched."""
    if not looks_like_chat_thread(raw):
        return raw
    out_lines = []
    current_name = None
    seen_names = []
    for line in raw.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        m = THREAD_HEADER_RE.match(line)
        if m:
            name = (m.group("name1") or m.group("name2") or m.group("name3") or "").strip()
            if name:
                current_name = name
                if name not in seen_names:
                    seen_names.append(name)
                    out_lines.append(f"{name}:")
            continue
        if current_name is None:
            continue
        # Strip a leading "Name:" repeated inline (common in some exports)
        msg = re.sub(rf'^{re.escape(current_name)}\s*:\s*', '', stripped)
        if msg and msg[0] not in "-•*":
            msg = f"- {msg}"
        elif not msg:
            continue
        out_lines.append(msg)
    return "\n".join(out_lines) if out_lines else raw


DAY_SEP_RE = re.compile(
    r'^\s*(?:[-=~_*]{2,}\s*)?'
    r'(?:(?:Mon|Tue|Wed|Thu|Fri|Sat|Sun)[a-zA-Z]*|Day\s*\d+|\d{1,2}[/-]\d{1,2}(?:[/-]\d{2,4})?)'
    r'\s*(?:[-=~_*]{2,})?\s*$',
    re.IGNORECASE
)


def split_multi_day_paste(raw: str):
    """Detects a bulk paste of several days' updates in one box (separated
    by a date/day-name line, e.g. 'Monday', 'Day 2', '15/09', '=== Tue ===')
    and splits it into (day_label, day_raw_text) segments. Returns an empty
    list when fewer than 2 segments are found, since a single day's paste
    should behave exactly as before."""
    lines = raw.splitlines()
    segments = []
    current_label = None
    current_lines = []
    for line in lines:
        stripped = line.strip()
        if stripped and DAY_SEP_RE.match(stripped):
            if current_lines and any(l.strip() for l in current_lines):
                segments.append((current_label or f"Day {len(segments)+1}", "\n".join(current_lines).strip()))
            current_label = stripped.strip("-=~_* ")
            current_lines = []
        else:
            current_lines.append(line)
    if current_lines and any(l.strip() for l in current_lines):
        segments.append((current_label or f"Day {len(segments)+1}", "\n".join(current_lines).strip()))
    return segments if len(segments) > 1 else []


DOMAIN_KEYWORDS = {
    "💻 Software Dev": ["deploy", "bug", "sprint", "merge", "pipeline", "api", "backend", "frontend", "code", "repo", "pr "],
    "🧪 QA / Testing": ["test case", "regression", "qa ", "test coverage", "bug report", "uat"],
    "🚀 DevOps":       ["infra", "kubernetes", "docker", "ci/cd", "server", "deployment", "monitoring"],
    "🎨 Design / UX":  ["wireframe", "prototype", "figma", "user test", "design review", "mockup"],
    "📦 Product":      ["roadmap", "backlog", "stakeholder", "feature spec", "user story"],
    "💰 Finance":      ["invoice", "budget", "reconcil", "forecast", "audit", "expense"],
    "🧩 Functional Team": ["coordinat", "escalat", "workflow", "operational", "process"],
    "🧑‍🤝‍🧑 Human Resource Team": ["onboard", "candidate", "interview", "recruit", "policy", "employee engagement", "grievance", "performance review"],
}


def suggest_domain(raw: str):
    """Best-effort domain guess from raw text keywords. Returns None if no clear signal."""
    if not raw.strip():
        return None
    text = raw.lower()
    scores = {d: sum(text.count(k) for k in kws) for d, kws in DOMAIN_KEYWORDS.items()}
    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else None


def looks_malformed(raw: str, members: list):
    """Returns a warning message if the raw input looks off, else None."""
    if not raw.strip():
        return None
    if not members:
        return "Could not detect any team member names. Use a 'Name:' header followed by '-' bullet points."
    if len(raw.strip().splitlines()) <= 2:
        return "This looks very short — make sure each person's tasks are on their own '-' bulleted lines."
    return None


def word_diff_html(old_text: str, new_text: str) -> tuple:
    """Word-level diff between two task strings, returned as (old_html,
    new_html) with removed words wrapped in a red strike-through span in
    old_html and added words wrapped in a green span in new_html — so the
    'vs yesterday' panel shows what actually changed, not just two full
    strings side by side."""
    import html as _html
    from difflib import SequenceMatcher
    old_words = old_text.split()
    new_words = new_text.split()
    sm = SequenceMatcher(None, old_words, new_words)
    old_parts, new_parts = [], []
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        old_chunk = _html.escape(" ".join(old_words[i1:i2]))
        new_chunk = _html.escape(" ".join(new_words[j1:j2]))
        if tag == "equal":
            old_parts.append(old_chunk)
            new_parts.append(new_chunk)
        else:
            # Semantic tags (<del>/<mark>) so removed/added words are
            # clearly highlighted even without the CSS (e.g. copy-pasted
            # elsewhere) — the diff-del/diff-add classes still carry the
            # actual strikethrough/highlight styling.
            if old_chunk:
                old_parts.append(f'<del class="diff-del">{old_chunk}</del>')
            if new_chunk:
                new_parts.append(f'<mark class="diff-add">{new_chunk}</mark>')
    return " ".join(old_parts), " ".join(new_parts)


def diff_against_previous(current_members: list, previous_entry: dict) -> dict:
    """
    For each person in current_members, finds tasks that closely match a
    task they had in the previous saved entry — signals possible carryover
    or a stalled task. Returns {name: [(today_task, yesterday_task), ...]}
    so the UI can show an actual before/after comparison, not just today's
    text in isolation.
    """
    if not previous_entry or not previous_entry.get("members_detail"):
        return {}
    from difflib import SequenceMatcher
    prev_by_name = {m["name"].lower(): m["tasks"] for m in previous_entry["members_detail"]}
    result = {}
    for m in current_members:
        prev_tasks = prev_by_name.get(m["name"].lower(), [])
        pairs = []
        for task in m["tasks"]:
            best_match, best_ratio = None, 0.0
            for prev_task in prev_tasks:
                ratio = SequenceMatcher(None, task.lower(), prev_task.lower()).ratio()
                if ratio > best_ratio:
                    best_match, best_ratio = prev_task, ratio
            if best_ratio > 0.6:
                pairs.append((task, best_match))
        if pairs:
            result[m["name"]] = pairs
    return result


def flag_brief_updates(current_members: list, history: list) -> dict:
    """
    Purely objective, quantitative comparison — NOT sentiment/emotion
    analysis. Flags when a person's update today has notably fewer words
    per task than their own historical average across saved entries. This
    is a factual verbosity observation only (e.g. "shorter than usual"),
    deliberately avoiding any inference about mood, stress, or wellbeing —
    a manager can use it as a cue to check in, not as a diagnosis.
    Returns {name: (today_avg_words, historical_avg_words)}.
    """
    if len(history) < 2:
        return {}  # need at least 2 past entries for a meaningful average

    word_counts_by_name = {}
    for entry in history:
        for m in entry.get("members_detail", []):
            name_key = m["name"].lower()
            if not m["tasks"]:
                continue
            avg_words = sum(len(t.split()) for t in m["tasks"]) / len(m["tasks"])
            word_counts_by_name.setdefault(name_key, []).append(avg_words)

    flagged = {}
    for m in current_members:
        key = m["name"].lower()
        past_avgs = word_counts_by_name.get(key, [])
        if len(past_avgs) < 2 or not m["tasks"]:
            continue
        historical_avg = sum(past_avgs) / len(past_avgs)
        today_avg = sum(len(t.split()) for t in m["tasks"]) / len(m["tasks"])
        if historical_avg > 4 and today_avg < historical_avg * 0.5:
            flagged[m["name"]] = (round(today_avg, 1), round(historical_avg, 1))
    return flagged


def flag_recurring_blockers(current_members: list, history: list) -> dict:
    """
    Flags a blocker as needing attention once a closely-matching blocker
    text has appeared for the same person across 1+ PRIOR saved entries
    (so 2+ days running including today) — surfaced as amber at 2 days and
    escalating to red at 3+ days by the caller's color logic. Uses the
    same fuzzy-match approach as diff_against_previous — this is about how
    long a blocker has persisted, not any judgment about why. Returns
    {name: [(blocker_text, days_seen), ...]} for blockers at or above the
    threshold.
    """
    if not history:
        return {}
    from difflib import SequenceMatcher
    escalations = {}
    for m in current_members:
        if not m.get("blockers"):
            continue
        name_key = m["name"].lower()
        for blocker in m["blockers"]:
            days_seen = 1  # today
            for entry in history:
                prev_blockers = next(
                    (pm["blockers"] for pm in entry.get("members_detail", [])
                     if pm["name"].lower() == name_key), []
                )
                if any(SequenceMatcher(None, blocker.lower(), pb.lower()).ratio() > 0.6
                       for pb in prev_blockers):
                    days_seen += 1
            if days_seen >= 2:
                escalations.setdefault(m["name"], []).append((blocker, days_seen))
    return escalations


def compute_health_score(members: list, brief_flags: dict, escalations: dict) -> tuple:
    """
    HEURISTIC ONLY — not a scientific metric, just a rough at-a-glance
    signal for the person reading the standup, computed purely from
    already-available counts (no AI call, no inference about anyone).

    Formula (0-100, higher = healthier):
      start at 100, then subtract:
        - 8 points per active blocker (capped at 40 off)
        - 15 points per recurring/escalated blocker (capped at 45 off)
        - 6 points per brief-update flag (capped at 24 off)
    Returns (score:int, label:str).
    """
    if not members:
        return 100, "No data"
    total_blockers = sum(len(m.get("blockers", [])) for m in members)
    score = 100
    score -= min(40, total_blockers * 8)
    score -= min(45, len(escalations) * 15)
    score -= min(24, len(brief_flags) * 6)
    score = max(0, min(100, score))
    if score >= 85:
        label = "Healthy"
    elif score >= 60:
        label = "Okay"
    elif score >= 35:
        label = "Strained"
    else:
        label = "At risk"
    return score, label


def flag_overload_trend(current_members: list, history: list) -> dict:
    """
    AGGREGATE, NON-DIAGNOSTIC early-warning cue only — reuses the same
    objective signals as flag_brief_updates()/flag_recurring_blockers()
    (word-count brevity and fuzzy-matched recurring blockers), plus a
    simple high-task-count check, looked at across the last ~2-3 saved
    entries (not all history) to spot someone trending toward overload.
    This is deliberately NOT sentiment analysis and NEVER labels or
    diagnoses a person — it only counts how many of these three
    objective, already-existing signals recurred for them recently, as a
    cue for the person running standup to maybe check in. Returns
    {name: [reason_str, ...]} only for members with 2+ recurring signals.
    Callers MUST keep this private (never put it in any exported/shared
    output) and MUST frame it as "worth checking in on", never a verdict.
    """
    if len(history) < 2:
        return {}
    brief_flags = flag_brief_updates(current_members, history)
    escalations = flag_recurring_blockers(current_members, history)

    # High task count: a person's recent average task count notably above
    # their own historical average (same "compare to their own baseline"
    # approach as flag_brief_updates, just on count instead of word-length).
    counts_by_name = {}
    for entry in history:
        for m in entry.get("members_detail", []):
            counts_by_name.setdefault(m["name"].lower(), []).append(len(m.get("tasks", [])))

    results = {}
    for m in current_members:
        key = m["name"].lower()
        reasons = []
        if m["name"] in brief_flags:
            reasons.append("shorter-than-usual updates recently")
        if m["name"] in escalations:
            reasons.append("a blocker has persisted across recent standups")
        past_counts = counts_by_name.get(key, [])
        if len(past_counts) >= 3:
            recent_avg = sum(past_counts[:3]) / 3
            overall_avg = sum(past_counts) / len(past_counts)
            if overall_avg > 0 and recent_avg > overall_avg * 1.5 and recent_avg >= 4:
                reasons.append("task count has been running well above their usual pace")
        if len(reasons) >= 2:
            results[m["name"]] = reasons
    return results


MENTION_RE = re.compile(r'@([A-Za-z][\w]{1,30})')


def tag_mentions(text: str, member_names: list) -> str:
    """
    Pure string matching (no AI call): turns '@Name' into a small visual
    pill when Name matches a detected team member (case-insensitive,
    first-name match is enough), used when rendering blocker/task text so
    e.g. 'blocked by @Bob' visually links to Bob's chip. HTML-escapes the
    surrounding text first since this output goes through unsafe_allow_html.
    """
    import html as _html
    name_lookup = {n.split()[0].lower(): n for n in member_names}
    escaped = _html.escape(text)

    def _sub(m):
        raw_name = m.group(1)
        match = name_lookup.get(raw_name.lower())
        if match:
            return f'<span class="mention-pill">@{_html.escape(match)}</span>'
        return m.group(0)

    return MENTION_RE.sub(_sub, escaped)


# ── ICEBREAKER / QUICK-QUESTION SUGGESTIONS ──
# Curated, rotates into the existing "Quick team question" text_input via
# the 🎲 Suggest button — no AI call needed, just a random pick.
ICEBREAKER_QUESTIONS = [
    "What's one small win from this week you haven't mentioned yet?",
    "Coffee, tea, or something else — what's keeping you going today?",
    "If you could automate away one annoying task, what would it be?",
    "What's a tool or shortcut you discovered recently that others should know about?",
    "Morning person or night owl?",
    "What's the last show/movie/book you'd actually recommend?",
    "If today had one extra hour, what would you spend it on?",
    "What's one thing you're looking forward to this week?",
    "Best meal you've had recently?",
    "What's your go-to focus music (or silence)?",
    "Any weekend plans worth sharing?",
    "What's a skill you'd like to pick up outside of work?",
    "Dogs, cats, or neither?",
    "What's the most useful piece of advice you've gotten this year?",
    "If you swapped roles with a teammate for a day, whose would you pick?",
    "What's one thing that would make this sprint smoother?",
    "Favorite way to unwind after a long day?",
    "What's a recent 'aha' moment you had while debugging or problem-solving?",
    "Thumbs up if Friday's demo time still works for everyone?",
    "What's one thing you're proud of from this sprint so far?",
]


# ── TEMPLATE / PRESET LIBRARY — same local-JSON persistence pattern as
# load_roster()/save_roster(). Stores {preset_name: {tone, domain, lang}}. ──
PRESETS_FILE = f".sanghastatus_presets{_TEAM_SUFFIX}.json"
GLOSSARY_FILE = f".sanghastatus_glossary{_TEAM_SUFFIX}.json"


def load_presets() -> dict:
    """Backed by the SQLite DB's "presets" table now; PRESETS_FILE is only
    read once, as a legacy fallback (see _kv_load_with_json_migration)."""
    return _kv_load_with_json_migration("presets", TEAM_SLUG, PRESETS_FILE, {})


def save_presets(presets: dict) -> None:
    try:
        _kv_set_raw("presets", TEAM_SLUG, presets)
    except Exception:
        pass


# ── TEAM GLOSSARY — same DB-backed persistence pattern as presets/roster.
# Stores [{"term": str, "expansion": str}, ...] so a team's jargon/acronyms
# get expanded verbatim by the LLM instead of being paraphrased away. ──
def load_glossary() -> list:
    return _kv_load_with_json_migration("glossary", TEAM_SLUG, GLOSSARY_FILE, [])


def save_glossary(glossary: list) -> None:
    try:
        _kv_set_raw("glossary", TEAM_SLUG, glossary)
    except Exception:
        pass


def glossary_prompt_block(glossary: list) -> str:
    """Deterministic prompt fragment listing the team's jargon so the LLM
    uses the team's own terms verbatim rather than paraphrasing them."""
    if not glossary:
        return ""
    lines = "\n".join(f'- "{g["term"]}" = {g["expansion"]}' for g in glossary if g.get("term"))
    return f"""
TEAM GLOSSARY — use these terms EXACTLY as written below whenever the raw input
uses them or clearly refers to them. Do not paraphrase or expand them differently:
{lines}
"""


ACTION_ITEM_RE = re.compile(
    r'\bwill\s+(?P<what>.+?)\s+by\s+(?P<when>tomorrow|today|tonight|'
    r'mon(?:day)?|tue(?:s(?:day)?)?|wed(?:nesday)?|thu(?:rs(?:day)?)?|fri(?:day)?|sat(?:urday)?|sun(?:day)?|'
    r'eod|eow|end of (?:day|week)|\d{1,2}[/-]\d{1,2}(?:[/-]\d{2,4})?)\b',
    re.IGNORECASE
)


def extract_action_items(members: list) -> list:
    """
    Pure-regex scan of each person's raw tasks for "will [do X] by [when]"
    phrasing — no AI call needed. Returns a list of {name, text, when} for
    a lightweight "reference tomorrow" checklist. Deliberately simple: it
    will miss action items phrased differently, which is fine for a quick
    cue rather than an exhaustive extraction.
    """
    items = []
    for m in members:
        for task in m.get("tasks", []):
            match = ACTION_ITEM_RE.search(task)
            if match:
                items.append({
                    "name": m["name"],
                    "text": match.group("what").strip(" .,"),
                    "when": match.group("when").strip().capitalize(),
                })
    return items


def check_action_item_followthrough(current_members: list, history: list) -> list:
    """
    For each action item extracted from YESTERDAY's saved entry (via
    extract_action_items, same regex, no AI call), fuzzy-matches its key
    phrase (SequenceMatcher, same approach as diff_against_previous() /
    flag_recurring_blockers() above) against TODAY's completed tasks for
    that same person. Returns [{name, text, when, done}, ...] so the
    action-items card can mark each "✅ appears done" vs "⏳ still open".
    Heuristic only — a fuzzy text match, not a verified completion.
    """
    if not history:
        return []
    from difflib import SequenceMatcher
    yesterday_items = extract_action_items(history[0].get("members_detail", []))
    results = []
    for item in yesterday_items:
        todays_tasks = next(
            (m.get("tasks", []) for m in current_members
             if m["name"].lower() == item["name"].lower()), []
        )
        done = any(
            SequenceMatcher(None, item["text"].lower(), t.lower()).ratio() > 0.45
            for t in todays_tasks
        )
        results.append({**item, "done": done})
    return results


def build_retro_export(history: list) -> str:
    """
    Deterministic aggregation of ALL saved history entries into a single
    'Sprint Retro' plain-text export — total tasks, total blockers, and a
    simple frequency count of repeated blocker text (recurring themes).
    Pure Python string processing, no extra LLM call, same pattern as
    to_jira_confluence_markup()/to_teams_markup() above.
    """
    if not history:
        return "No saved standups yet — nothing to include in a retro."
    from collections import Counter
    lines = ["SPRINT RETRO", "=" * 40, ""]
    total_tasks = sum(e.get("tasks", 0) for e in history)
    total_members_seen = len({
        m["name"].lower() for e in history for m in e.get("members_detail", [])
    })
    blocker_counter = Counter()
    total_blockers = 0
    for e in history:
        for m in e.get("members_detail", []):
            for b in m.get("blockers", []):
                total_blockers += 1
                blocker_counter[b.strip().lower()] += 1

    lines.append(f"Standups included: {len(history)}")
    lines.append(f"Date range: {history[-1].get('date','?')} → {history[0].get('date','?')}")
    lines.append(f"Unique team members: {total_members_seen}")
    lines.append(f"Total tasks reported: {total_tasks}")
    lines.append(f"Total blockers reported: {total_blockers}")
    lines.append("")
    lines.append("RECURRING THEMES (blocker text seen more than once)")
    lines.append("-" * 40)
    recurring = [(txt, n) for txt, n in blocker_counter.most_common() if n > 1]
    if recurring:
        for txt, n in recurring:
            lines.append(f"- ({n}x) {txt}")
    else:
        lines.append("No blocker text repeated across saved standups.")
    lines.append("")
    lines.append("PER-STANDUP SUMMARY")
    lines.append("-" * 40)
    for e in reversed(history):
        lines.append(f"📅 {e.get('date','?')} — {e.get('project','—')} — "
                      f"{e.get('members',0)} members, {e.get('tasks',0)} tasks")
    return "\n".join(lines)


def call_llm_retro_themes(history: list):
    """
    Genuine LLM-based theme analysis, as an alternative/upgrade alongside
    (not replacing) build_retro_export()'s deterministic frequency count.
    ONE call, sending all aggregated blocker + task text from saved
    history, asking for real recurring-theme analysis (e.g. "3 of 5
    blockers this sprint were environment-access related") rather than
    just counting exact-text repeats. Follows the same client/call
    pattern as call_llm_json() above, but the output here is prose, not
    strict JSON, so it calls the client directly instead. Returns
    (themes_text, error_str) — exactly one of which is truthy — so the
    caller can show a graceful error instead of crashing, same as the
    retry/except handling around the main generation call below.
    """
    if not history:
        return None, "No saved standups yet — nothing to analyze."

    all_tasks, all_blockers = [], []
    for e in history:
        for m in e.get("members_detail", []):
            all_tasks.extend(m.get("tasks", []))
            all_blockers.extend(m.get("blockers", []))

    if not all_tasks and not all_blockers:
        return None, "No task or blocker text in saved history to analyze."

    user_prompt = (
        f"BLOCKERS ACROSS THE SPRINT ({len(all_blockers)} total):\n"
        + "\n".join(f"- {b}" for b in all_blockers[:200])
        + f"\n\nTASKS ACROSS THE SPRINT ({len(all_tasks)} total):\n"
        + "\n".join(f"- {t}" for t in all_tasks[:300])
    )
    system_prompt = (
        "You are analyzing a software/product team's sprint retro data (aggregated blockers "
        "and tasks from several daily standups). Identify genuine RECURRING THEMES — not a "
        "restatement of every line. Group related items and quantify them, e.g. "
        "'3 of 5 blockers this sprint were environment-access related.' Call out: (1) the "
        "top 2-4 recurring blocker themes with counts, (2) the top 2-3 recurring work-focus "
        "themes, (3) one or two brief, constructive suggestions. Keep it objective and "
        "aggregate — never single out or characterize any one person. Plain text only, "
        "short headed sections, no markdown tables, no preamble."
    )
    try:
        completion = client.chat.completions.create(
            model="nvidia/nemotron-3.5-lightning-30b-a3b",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.3,
            max_tokens=700,
        )
        text = completion.choices[0].message.content.strip()
        text = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL).strip()
        if not text:
            return None, "The model returned an empty response — try again."
        return text, None
    except Exception as e:
        return None, f"Couldn't reach the AI model: {e}"


def dynamic_ta_height(text: str, min_h: int = 120, max_h: int = 500) -> int:
    """
    Sizes a text_area to fit its actual content instead of a fixed height
    that clips longer generations — counts wrapped lines (~90 chars/line)
    plus explicit newlines, at ~24px per line, clamped to a sane range.
    """
    if not text:
        return min_h
    line_count = 0
    for line in text.splitlines():
        line_count += max(1, -(-len(line) // 90))  # ceil division for wrapping
    return max(min_h, min(max_h, line_count * 24 + 40))


def to_jira_confluence_markup(chat_update: str) -> str:
    """
    Deterministic transform of the already-generated chat_update text into
    Jira/Confluence wiki markup — no extra LLM call needed, so it's instant.
    "• Name" -> "h3. Name" ; "- task" -> "* task"
    """
    out_lines = []
    for line in chat_update.splitlines():
        stripped = line.strip()
        if stripped.startswith("•"):
            out_lines.append(f"h3. {stripped.lstrip('•').strip()}")
        elif stripped.startswith("-"):
            out_lines.append(f"* {stripped.lstrip('-').strip()}")
        elif stripped:
            out_lines.append(f"h2. {stripped}")
        else:
            out_lines.append("")
    return "\n".join(out_lines)


def to_teams_markup(chat_update: str) -> str:
    """
    Deterministic transform into Microsoft Teams-flavored markdown.
    Teams supports standard markdown headers/bullets, so this mainly
    upgrades "• Name" lines to a bold sub-heading and keeps bullets as-is.
    """
    out_lines = []
    for line in chat_update.splitlines():
        stripped = line.strip()
        if stripped.startswith("•"):
            out_lines.append(f"**{stripped.lstrip('•').strip()}**")
        elif stripped.startswith("-"):
            out_lines.append(f"- {stripped.lstrip('-').strip()}")
        elif stripped:
            out_lines.append(f"### {stripped}")
        else:
            out_lines.append("")
    return "\n".join(out_lines)


def to_discord_markup(chat_update: str) -> str:
    """
    Deterministic transform into Discord-flavored markdown. Discord has no
    H1/H2, so section titles become bold-underline, names become bold, and
    a blockquote (">") style is used for the header line for visual pop.
    """
    out_lines = []
    for line in chat_update.splitlines():
        stripped = line.strip()
        if stripped.startswith("•"):
            out_lines.append(f"**{stripped.lstrip('•').strip()}**")
        elif stripped.startswith("-"):
            out_lines.append(f"• {stripped.lstrip('-').strip()}")
        elif stripped:
            out_lines.append(f"__**{stripped}**__")
        else:
            out_lines.append("")
    return "\n".join(out_lines)


def build_docx_export(data: dict, fmt_date: str, prepared_by: str = "", template: str = "Standup", blocker_meta=None, project: str = ""):
    """Builds a Word document from the generated status update. Returns
    (bytes, None) on success, or (None, error_message) if python-docx
    isn't installed in this environment."""
    try:
        from docx import Document
        import io as _io
    except ImportError:
        return None, "python-docx isn't installed — add 'python-docx' to requirements.txt to enable this."

    tpl = TEMPLATES.get(template, TEMPLATES["Standup"])
    doc = Document()
    doc.add_heading(f"{tpl['title']} — {fmt_date}", level=1)
    _sub = " · ".join(x for x in [project and f"Project: {project}", prepared_by and f"Prepared by {prepared_by}"] if x)
    if _sub:
        p = doc.add_paragraph()
        p.add_run(_sub).italic = True

    doc.add_heading(tpl["narr_title"], level=2)
    doc.add_paragraph(data.get("standup_narrative", ""))

    if data.get("tomorrow_plan"):
        doc.add_heading(tpl["tomorrow_title"], level=2)
        doc.add_paragraph(data["tomorrow_plan"])

    if data.get("blocker_summary") or blocker_meta:
        doc.add_heading(tpl["blockers_title"], level=2)
        if data.get("blocker_summary"):
            doc.add_paragraph(data["blocker_summary"])
        if blocker_meta:
            tbl = doc.add_table(rows=1, cols=4)
            tbl.style = "Table Grid"
            for i, h in enumerate(("Person", "Blocker", "Owner", "Needed by")):
                tbl.rows[0].cells[i].text = h
            for x in blocker_meta:
                cells = tbl.add_row().cells
                cells[0].text, cells[1].text = x.get("name", ""), x.get("blocker", "")
                cells[2].text, cells[3].text = x.get("owner") or "—", x.get("needs_by_date") or x.get("needs_by") or "—"

    doc.add_heading("Chat Update", level=2)
    doc.add_paragraph(data.get("chat_update", ""))

    doc.add_heading("Email Update", level=2)
    doc.add_paragraph(data.get("email_update", ""))

    buf = _io.BytesIO()
    doc.save(buf)
    buf.seek(0)
    return buf.read(), None


def build_pdf_export(data: dict, fmt_date: str, prepared_by: str = "", project: str = "", logo: bytes = None,
                     template: str = "Standup", blocker_meta=None):
    """
    Single-day PDF export (fpdf2). Branded: optional team logo + project name in a header and a page-numbered
    footer on EVERY page. Returns (bytes, None) on success, or (None, error_message) if fpdf2 isn't installed.
    Latin-1 core fonts only: characters outside Latin-1 (emoji, Devanagari) are dropped rather than crashing.
    """
    try:
        from fpdf import FPDF
        import io as _io
    except ImportError:
        return None, "fpdf2 isn't installed — add 'fpdf2' to sangha_requirements.txt to enable this (the .docx export above works meanwhile)."

    def _latin1(text: str) -> str:
        return (text or "").encode("latin-1", "ignore").decode("latin-1")

    tpl = TEMPLATES.get(template, TEMPLATES["Standup"])
    brand = _latin1(project) or "SanghaStatus"
    logo_wh = None
    if logo:
        try:
            from PIL import Image
            _im = Image.open(_io.BytesIO(logo))
            logo_wh = _im.size
        except Exception:
            logo = None

    class _BrandPDF(FPDF):
        def header(self):
            x = self.l_margin
            if logo and logo_wh:
                h = 12.0
                w = min(42.0, h * logo_wh[0] / max(1, logo_wh[1]))
                try:
                    self.image(_io.BytesIO(logo), x=x, y=8, w=w, h=h if w < 42.0 else None)
                    x += w + 4
                except Exception:
                    pass
            self.set_xy(x, 9)
            self.set_font("Helvetica", "B", 12)
            self.cell(0, 6, brand, new_x="LMARGIN", new_y="NEXT")
            self.set_x(x)
            self.set_font("Helvetica", "", 9)
            self.cell(0, 5, _latin1(f"{tpl['title']} - {fmt_date}"), new_x="LMARGIN", new_y="NEXT")
            self.line(self.l_margin, 24, self.w - self.r_margin, 24)
            self.set_y(28)

        def footer(self):
            self.set_y(-13)
            self.set_font("Helvetica", "I", 8)
            self.cell(0, 8, f"{brand}  |  Page {self.page_no()}/{{nb}}", align="C")

    pdf = _BrandPDF()
    pdf.alias_nb_pages()
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 16)
    pdf.multi_cell(0, 10, _latin1(f"{tpl['title']} - {fmt_date}"), new_x="LMARGIN", new_y="NEXT")
    if prepared_by:
        pdf.set_font("Helvetica", "I", 10)
        pdf.multi_cell(0, 8, _latin1(f"Prepared by {prepared_by}"), new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)

    def _section(title, body):
        if not body:
            return
        pdf.set_font("Helvetica", "B", 13)
        pdf.multi_cell(0, 9, _latin1(title), new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", "", 10)
        pdf.multi_cell(0, 6, _latin1(body), new_x="LMARGIN", new_y="NEXT")
        pdf.ln(3)

    _section(tpl["narr_title"], data.get("standup_narrative", ""))
    _section("Chat Update", data.get("chat_update", ""))
    _section(tpl["blockers_title"], data.get("blocker_summary", ""))
    if blocker_meta:
        _section("Blocker owners", "\n".join(
            f"- {x.get('name', '')}: {x.get('blocker', '')} | owner: {x.get('owner') or '-'} | needed by: {x.get('needs_by_date') or x.get('needs_by') or '-'}"
            for x in blocker_meta))

    return bytes(pdf.output()), None


@st.cache_data(show_spinner=False, max_entries=8)
def _cached_docx(data_json, fmt_date, prepared_by, template, meta_json="[]", project=""):
    return build_docx_export(json.loads(data_json), fmt_date, prepared_by, template, json.loads(meta_json), project)


@st.cache_data(show_spinner=False, max_entries=8)
def _cached_pdf(data_json, fmt_date, prepared_by, project, logo_bytes, template, meta_json):
    return build_pdf_export(json.loads(data_json), fmt_date, prepared_by, project, logo_bytes or None, template, json.loads(meta_json))


@st.cache_data(show_spinner=False, max_entries=16)
def _cached_consistency(members_json, texts_json):
    return consistency_check(json.loads(members_json), json.loads(texts_json))


def render_copy_button(text: str, unique_key: str, label: str = "Copy", html: str = None):
    """Small pill copy-to-clipboard button. The label flips to "Copied" with a green confirmation.
    With `html`, writes BOTH text/html and text/plain via ClipboardItem (rich paste into Confluence/Notion)
    and falls back to plain text where ClipboardItem or the permission is unavailable.
    Copies the text as generated (not live edits made in the paired text_area). Colours follow the app's
    active theme (read from the parent page's dark-mode switch) so contrast holds in every OS/app combination."""
    uk = re.sub(r'\W', '_', unique_key)
    payload = json.dumps(text)
    html_payload = json.dumps(html) if html else "null"
    components.html(f"""
    <div style="font-family:-apple-system,BlinkMacSystemFont,'SF Pro Text',Inter,'Segoe UI',Roboto,sans-serif;">
        <button id="copyBtn_{uk}" type="button" aria-label="{_html.escape(label)}"
            style="padding:7px 18px;border-radius:999px;border:0;cursor:pointer;font-size:0.84rem;font-weight:600;
            transition:transform 0.18s cubic-bezier(0.22,1,0.36,1), background 0.18s;"
            onmousedown="this.style.transform='scale(0.98)'" onmouseup="this.style.transform='none'">{_html.escape(label)}</button>
    </div>
    <script>
        const btn = document.getElementById('copyBtn_{uk}');
        const LABEL = {json.dumps(label)};
        let flash = false;
        function isDark() {{
            try {{ return !!window.parent.document.getElementById('dmchk').checked; }} catch (e) {{
                return !!(window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches); }}
        }}
        function paint() {{
            if (flash) return;
            const d = isDark();
            btn.style.background = d ? 'rgba(240,149,111,0.20)' : 'rgba(180,80,45,0.12)';
            btn.style.color = d ? '#f7b394' : '#8f3416';
        }}
        paint(); setInterval(paint, 700);
        function done(ok) {{
            flash = true;
            btn.textContent = ok ? 'Copied' : 'Copy failed';
            btn.style.background = ok ? '#1f7a3a' : '#b91c1c'; btn.style.color = '#fff';
            setTimeout(() => {{ flash = false; btn.textContent = LABEL; paint(); }}, 1400);
        }}
        function legacy(t) {{
            try {{ const ta = document.createElement('textarea'); ta.value = t; document.body.appendChild(ta); ta.select();
                  const ok = document.execCommand('copy'); document.body.removeChild(ta); return ok; }} catch (e) {{ return false; }}
        }}
        btn.addEventListener('click', async () => {{
            const text = {payload}, html = {html_payload};
            try {{
                if (html && window.ClipboardItem && navigator.clipboard && navigator.clipboard.write) {{
                    await navigator.clipboard.write([new ClipboardItem({{
                        'text/html': new Blob([html], {{type: 'text/html'}}),
                        'text/plain': new Blob([text], {{type: 'text/plain'}}) }})]);
                    return done(true);
                }}
            }} catch (e) {{ /* fall through to plain text */ }}
            try {{ await navigator.clipboard.writeText(text); return done(true); }} catch (e) {{ return done(legacy(text)); }}
        }});
    </script>
    """, height=44)


def mailto_link(subject: str, body: str) -> str:
    s = urllib.parse.quote(subject)
    b = urllib.parse.quote(body)
    return f"mailto:?subject={s}&body={b}"


def render_loader(stage_idx: int) -> str:
    total = len(LOADER_STAGES)
    emoji, title, sub = LOADER_STAGES[stage_idx]
    pct = int((stage_idx + 1) / total * 100)
    dots = "".join([
        f'<div class="ld {"ldone" if i < stage_idx else ("lactive" if i == stage_idx else "")}"></div>'
        for i in range(total)
    ])
    n_micro = len(LOADER_MICRO_COPY)
    slot_secs = 2.5
    loop_secs = n_micro * slot_secs
    micro_spans = "".join(
        f'<span class="loader-micro-item" style="animation-duration:{loop_secs}s;'
        f'animation-delay:-{i*slot_secs}s;">{line}</span>'
        for i, line in enumerate(LOADER_MICRO_COPY)
    )
    return (
        f'<div class="loader-wrap">'
        f'<div class="loader-emoji">{emoji}</div>'
        f'<div class="loader-title">{title}</div>'
        f'<div class="loader-sub">{sub} &nbsp;·&nbsp; {stage_idx+1}/{total}</div>'
        f'<div class="loader-micro">{micro_spans}</div>'
        f'<div class="loader-dots">{dots}</div>'
        f'<div class="loader-bar-bg"><div class="loader-bar-fg" style="width:{pct}%"></div></div>'
        f'<div class="loader-pct">{pct}%</div>'
        f'</div>'
    )


# ═══════════════════════════════════════════════════
# SYSTEM PROMPT
# ═══════════════════════════════════════════════════
def extract_json_object(raw: str) -> dict:
    """
    Robustly parse a JSON object from an LLM response. Some models
    (e.g. reasoning models like Nemotron 3.5 Lightning) prepend a
    <think>...</think> block before the actual JSON, or wrap the JSON
    in markdown code fences — both of which break a plain json.loads.
    This strips those, then extracts the {...} substring before parsing.
    """
    s = raw.strip()

    # Strip a <think>...</think> block if present (even if unterminated —
    # in that case drop everything up to the last </think> or, if there's
    # no closing tag at all, take everything after the LAST '}' as a
    # fallback isn't reliable, so just remove the tag pair when found).
    s = re.sub(r'<think>.*?</think>', '', s, flags=re.DOTALL)
    s = re.sub(r'^.*?</think>', '', s, count=1, flags=re.DOTALL)  # unterminated opening tag case

    # Strip markdown code fences (```json ... ``` or ``` ... ```)
    s = re.sub(r'^```(?:json)?\s*', '', s.strip())
    s = re.sub(r'```\s*$', '', s.strip())

    s = s.strip()

    # Extract the outermost {...} in case there's any leftover stray text
    start = s.find('{')
    end = s.rfind('}')
    if start != -1 and end != -1 and end > start:
        s = s[start:end + 1]

    return json.loads(s)


def call_llm_json(system_prompt: str, user_prompt: str, temperature: float, max_tokens: int):
    """
    Calls the LLM and returns the parsed JSON dict. Tries to disable the
    model's reasoning/thinking mode via extra_body first (Nemotron 3.5
    Lightning is a hybrid reasoning model that can otherwise prepend a
    <think>...</think> block before the JSON); if the server rejects that
    parameter, retries once without it. extract_json_object() strips any
    leftover <think> block regardless, as a safety net either way.
    """
    kwargs = dict(
        model="nvidia/nemotron-3.5-lightning-30b-a3b",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        temperature=temperature,
        max_tokens=max_tokens,
        response_format={"type": "json_object"},
    )
    try:
        completion = client.chat.completions.create(
            **kwargs, extra_body={"chat_template_kwargs": {"thinking": False}}
        )
    except Exception:
        completion = client.chat.completions.create(**kwargs)

    data = extract_json_object(completion.choices[0].message.content)
    return data, completion


def _shared_instructions(tone: str, domain: str, lang: str, glossary_block: str = "") -> str:
    """Common domain/tone/language framing reused by all three split prompts."""
    return f"""{glossary_block}
You are SanghaStatus, a precise professional assistant for workplace teams.

DOMAIN CONTEXT: You are writing updates for a {domain} team.
Use vocabulary, phrasing, and framing natural to this domain. For example:
- Software Dev / QA / DevOps: use terms like "deployed", "resolved", "tested", "merged", "pipeline", "sprint".
- Functional Team: use terms like "coordinated", "aligned with stakeholders", "processed", "escalated", "streamlined workflow", "operational milestone".
- Human Resource Team: use terms like "onboarded", "screened candidates", "conducted interviews", "policy rollout", "employee engagement", "performance review", "grievance resolved" — and NEVER use software/technical jargon (no "deployed", "bug", "sprint", etc.) unless the raw input explicitly mentions it.
- Finance: use terms like "reconciled", "audited", "processed invoices", "forecasted", "budget review".
- Design/UX: use terms like "prototyped", "wireframed", "user tested", "iterated on design".
Always stay faithful to what the raw input actually says — domain vocabulary should make the phrasing natural, not invent activities that didn't happen.

TONE: {tone}
OUTPUT LANGUAGE: Write ALL output fields in {lang}.

STRICT RULES:
- TRANSFORM RAW INPUTS: DO NOT just copy-paste the raw bullet points. You MUST rewrite and expand every single short phrase into a full, professional, action-oriented sentence ending with a period.
  * Bad: "- Support for testing activities"
  * Good: "- Provided support for testing activities, ensuring test coverage stayed on track."
  * Bad: "- working on masking"
  * Good: "- Currently working on implementing masking enhancements."
- Every single bullet — including the LAST one in a person's list — must be fully rewritten this way. Do not leave any bullet as a bare noun phrase or fragment from the raw input; every bullet must start with a past- or present-tense action verb.
- Each raw task stays as its own separate bullet. Do NOT merge tasks or summarize multiple tasks into one.
- Keep each person's updates strictly separated under their name.
- Use correct pronouns inferred from context, or use their name if unclear.
- NO introductory or concluding conversational text in the JSON values.
- Return ONLY a valid JSON object — no markdown fences, no preamble.
- Do NOT include any reasoning, chain-of-thought, or <think> tags of any kind in your response — output ONLY the raw JSON object and nothing else, starting with {{ and ending with }}.
- Every sentence must be grammatically complete — never truncate or cut a sentence short partway through.
"""


def build_narrative_prompt(tone, domain, lang, include_tomorrow, include_blockers, glossary_block="", template="Standup"):
    """Narrative-family output: the spoken standup, tomorrow's plan, blockers.
    Split out so it can run in parallel with the chat/email prompts below."""
    tomorrow_key = (
        ',\n  "tomorrow_plan": "Good morning, everyone.\\n\\n[Name 1] plans to [tomorrow task].\\n[Name 2] plans to [tomorrow task].\\n\\nThat concludes the plan for tomorrow."'
        if include_tomorrow else ""
    )
    blocker_key = (
        ',\n  "blocker_summary": "Blockers identified today:\\n\\n[Name]: [Blocker detail].\\n(Write \\"No blockers reported today.\\" if none)"'
        if include_blockers else ""
    )
    blocker_guidance = (
        """
BLOCKER DETECTION: Identify blockers by MEANING, not by keyword-matching. A task
is a blocker if it describes being stuck, waiting, or unable to proceed —
including phrasing that doesn't contain an obvious keyword like "block", e.g.:
- "Waiting on the vendor to confirm pricing" → blocker (waiting on external party)
- "Need approval from finance before proceeding" → blocker (needs approval)
- "Access request still pending with IT" → blocker (pending access)
- "Can't reproduce the issue without prod data" → blocker (missing dependency)
Do NOT treat a task as a blocker just because it mentions a bug or issue being
WORKED ON or RESOLVED — only flag it if the person is genuinely stuck/waiting.
"""
        if include_blockers else ""
    )
    return _shared_instructions(tone, domain, lang, glossary_block) + blocker_guidance + f"""
Return a JSON object with EXACTLY these keys:
{{
  "standup_narrative": "Good morning, everyone.\\n\\nHere is the status update for [Date].\\n\\n[Name 1]: [narrative].\\n\\n[Name 2]: [narrative].\\n\\nThat concludes today's status update."{tomorrow_key}{blocker_key}
}}
""" + template_prompt_block(template, "narrative")


def build_chat_prompt(tone, domain, lang, glossary_block="", template="Standup"):
    """Chat-family output: Slack/Teams update + WhatsApp update.
    Runs in parallel with the narrative and email prompts."""
    return _shared_instructions(tone, domain, lang, glossary_block) + """
Use hyphen "-" for bullets. Never asterisks in chat_update (WhatsApp update may use *bold* for names).
IMPORTANT: each person's name/header appears ONLY ONCE, with ALL of their tasks listed as bullets underneath it — never repeat a person's name header for each separate task.
REMINDER — REWRITE, DO NOT COPY: every bullet must be your own rewritten, full sentence — never the raw input text with only capitalization/punctuation fixed.

Return a JSON object with EXACTLY these keys:
{
  "chat_update": "Daily Project Status Update | [Date]\\n\\n• [Name 1]\\n- [Task 1 sentence].\\n- [Task 2 sentence].\\n\\n• [Name 2]\\n- [Task 1 sentence].",
  "whatsapp_update": "📋 *Daily Status Update | [Date]*\\n\\n*[Name 1]*\\n- [Task 1 sentence].\\n- [Task 2 sentence].\\n\\n*[Name 2]*\\n- [Task 1 sentence]."
}
""" + template_prompt_block(template, "chat")


def build_email_prompt(tone, domain, lang, glossary_block="", template="Standup"):
    """Email-family output. Runs in parallel with the narrative and chat prompts."""
    return _shared_instructions(tone, domain, lang, glossary_block) + """
Use hyphen "-" for bullets. Never asterisks.

REMINDER — REWRITE, DO NOT COPY: The bullets under [Task 1], [Task 2] etc. must be your OWN
rewritten, full, professional sentences — never the raw input text verbatim, even with minor
punctuation fixes. If a raw line reads "-Worked on the Data migration activity", the email
bullet must be substantively rewritten (e.g. "- Led the data migration effort, ensuring a
smooth transition of records.") — not simply recapitalized and given a period. Every bullet in
the email must sound like it came from a professional writer, not a copy-paste of the input.

SIGN-OFF RULE: The email is being SENT ABOUT the team members listed, not BY one of them —
never sign the closing with any of the team members' own names, since that would make it
look like a team member is reporting on themselves to the team. Always close with a generic
sign-off that names no individual, exactly: "Regards,\\nProject Team" — do not substitute any
person's name here under any circumstances, even if only one team member was mentioned.

Return a JSON object with EXACTLY this key:
{
  "email_update": "Subject: Daily Project Status Update | [Date]\\n\\nDear Team,\\n\\nPlease find below the status update for [Date].\\n\\n[Name 1]\\n- [Fully rewritten task sentence, not a copy of the input].\\n\\n[Name 2]\\n- [Fully rewritten task sentence].\\n\\nKindly revert in case of any queries.\\n\\nRegards,\\nProject Team"
}
""" + template_prompt_block(template, "email")


# ═══════════════════════════════════════════════════════════════════
# ITERATION A HELPERS — writing quality. All pure/deterministic except the
# two LLM wrappers (revise_output / audience_rewrite), which are only ever
# called from their own buttons.
# ═══════════════════════════════════════════════════════════════════
from datetime import timedelta
from difflib import SequenceMatcher as _SM

# ── 35: sensitive-data scrubber ──
_SENS_RULES = [
    ("API-KEY",      re.compile(r'\b(?:sk|nvapi|pk|rk)-[A-Za-z0-9_\-]{16,}'), 0),
    ("GITHUB-TOKEN", re.compile(r'\b(?:gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,})'), 0),
    ("AWS-KEY",      re.compile(r'\b(?:AKIA|ASIA)[0-9A-Z]{16}\b'), 0),
    ("SLACK-TOKEN",  re.compile(r'\bxox[abprs]-[A-Za-z0-9-]{10,}'), 0),
    ("JWT",          re.compile(r'\beyJ[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}'), 0),
    ("PASSWORD",     re.compile(r'(?i)\b(?:password|passwd|pwd|passcode)\s*(?:is\b|[:=])\s*["\']?([^\s"\',;]{3,})'), 1),
    ("SECRET",       re.compile(r'(?i)\b(?:secret|api[_ -]?key|token)\s*[:=]\s*["\']?([^\s"\',;]{6,})'), 1),
    ("HEX-SECRET",   re.compile(r'\b[a-fA-F0-9]{32,}\b'), 0),
    ("LONG-TOKEN",   re.compile(r'(?<![\w/+=-])(?=[A-Za-z0-9+/_-]*[A-Za-z])(?=[A-Za-z0-9+/_-]*\d)[A-Za-z0-9+/_-]{40,}={0,2}(?![\w])'), 0),
    ("EMAIL",        re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b'), 0),
]
_PHONE_RE = re.compile(r'(?<![\w.@/-])(\+?\d[\d\s().-]{7,17}\d)(?![\w@])')


def _phone_ok(m: str) -> bool:
    digits = re.sub(r'\D', '', m)
    if not (10 <= len(digits) <= 13):
        return False
    return not re.fullmatch(r'\d{4}[-/]\d{2}[-/]\d{2}', m.strip())


def mask_sensitive(text: str):
    """Returns (masked_text, findings). findings = [{type, preview, count}]. Placeholders look
    like [REDACTED-API-KEY]. Pure function — callers decide whether to use the masked copy."""
    found = {}

    def _note(kind, val):
        d = found.setdefault(kind, {"type": kind, "preview": (val[:4] + "…") if len(val) > 4 else "…", "count": 0})
        d["count"] += 1

    out = text or ""
    for kind, rx, grp in _SENS_RULES:
        def _sub(m, kind=kind, grp=grp):
            val = m.group(grp or 0)
            _note(kind, val)
            if grp:
                whole = m.group(0)
                i = whole.rfind(val)
                return whole[:i] + f"[REDACTED-{kind}]" + whole[i + len(val):]
            return f"[REDACTED-{kind}]"
        out = rx.sub(_sub, out)

    def _ph(m):
        if _phone_ok(m.group(1)):
            _note("PHONE", m.group(1))
            return "[REDACTED-PHONE]"
        return m.group(0)
    out = _PHONE_RE.sub(_ph, out)
    return out, list(found.values())


# ── 24: metrics ("By the numbers") ──
_MET_NOUNS = {
    "ticket": "tickets", "issue": "tickets", "story": "tickets",
    "bug": "bugs", "defect": "bugs",
    "test": "tests",
    "pr": "PRs", "pull request": "PRs",
    "deploy": "deploys", "deployment": "deploys", "release": "releases",
    "candidate": "candidates", "interview": "interviews", "invoice": "invoices",
}
_MET_NOUN_RX = r'(?:tickets?|issues?|stories|story|bugs?|defects?|tests?(?:\s+cases?)?|prs?|pull\s+requests?|deploy(?:s|ments?)?|releases?|candidates?|interviews?|invoices?)'
_MET_VERB_RX = r'(?:closed|resolved|fixed|merged|passed|passing|deployed|completed|shipped|reviewed|screened|processed|released|done)'
_MET_A = re.compile(r'\b' + _MET_VERB_RX + r'\s+(\d+)\s+(?:\w+\s+)?(' + _MET_NOUN_RX + r')\b', re.I)
_MET_B = re.compile(r'\b(\d+)\s+(?:\w+\s+)?(' + _MET_NOUN_RX + r')(?:\s+(' + _MET_VERB_RX + r'))?\b', re.I)
_MET_VERB_LABEL = {
    ("tickets", "closed"): "tickets closed", ("tickets", "resolved"): "tickets closed", ("tickets", "done"): "tickets closed", ("tickets", "completed"): "tickets closed",
    ("bugs", "fixed"): "bugs fixed", ("bugs", "resolved"): "bugs fixed", ("bugs", "closed"): "bugs fixed",
    ("tests", "passed"): "tests passed", ("tests", "passing"): "tests passed",
    ("PRs", "merged"): "PRs merged", ("PRs", "reviewed"): "PRs reviewed",
    ("deploys", "deployed"): "deploys", ("deploys", "completed"): "deploys",
    ("releases", "deployed"): "releases", ("releases", "released"): "releases", ("releases", "shipped"): "releases",
}


def _canon_noun(n: str) -> str:
    n = re.sub(r'\s+', ' ', n.lower().strip())
    if n.startswith("test"):
        return "tests"
    if n.startswith("deploy"):
        return "deploys"
    if n in ("prs", "pr"):
        return "PRs"
    if n.startswith("pull"):
        return "PRs"
    if n in ("stories", "story"):
        return "tickets"
    if n.endswith("ies"):
        n = n[:-3] + "y"
    elif n.endswith("s") and not n.endswith("ss"):
        n = n[:-1]
    return _MET_NOUNS.get(n, n)


def extract_metrics(members: list) -> list:
    """Deterministic: pulls '<number> <noun>' facts out of the raw notes. Returns [(label, total)],
    e.g. [('tickets closed', 5), ('tests passed', 12)]. Never invents a number."""
    totals = {}
    for m in members:
        for t in m.get("tasks", []):
            spans = []
            for rx, vi in ((_MET_A, None), (_MET_B, 3)):
                for mt in rx.finditer(t):
                    if any(mt.start() < e and s < mt.end() for s, e in spans):
                        continue
                    spans.append((mt.start(), mt.end()))
                    n = int(mt.group(1))
                    noun = _canon_noun(mt.group(2))
                    verb = (mt.group(0).split()[0] if vi is None else (mt.group(3) or "")).lower()
                    label = _MET_VERB_LABEL.get((noun, verb)) or (f"{noun} {verb}".strip() if verb else noun)
                    totals[label] = totals.get(label, 0) + n
    return sorted(totals.items(), key=lambda kv: -kv[1])


# ── 25: relative dates → concrete dates ──
_WD_NAMES = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
_WD_PAT = r'(?:mon(?:day)?|tue(?:s(?:day)?)?|wed(?:nesday)?|thu(?:r(?:s(?:day)?)?)?|fri(?:day)?|sat(?:urday)?|sun(?:day)?)'
_DATE_PHRASE_RE = re.compile(
    r'\b(?P<pre>by|before|until|till|due|on|for)?\s*(?P<p>tomorrow|today|tonight|eod|eow|cob|end of (?:the )?(?:day|week)|next week|'
    r'next ' + _WD_PAT + r'|' + _WD_PAT + r'|\d{1,2}[/-]\d{1,2}(?:[/-]\d{2,4})?)\b', re.I)


def _wd_index(word: str):
    w = word.lower()[:3]
    for i, n in enumerate(_WD_NAMES):
        if n.startswith(w):
            return i
    return None


def resolve_date_phrase(phrase: str, base: date):
    """Resolve 'tomorrow' / 'by Friday' / 'next week' / 'EOD' / '12/11' relative to `base` (the standup
    date). A bare weekday resolves to its next occurrence (today if it IS that weekday); 'next <weekday>'
    is that weekday in the following week; 'next week' is the coming Monday."""
    p = (phrase or "").strip().lower()
    if p in ("today", "tonight", "eod", "cob", "end of day", "end of the day"):
        return base
    if p == "tomorrow":
        return base + timedelta(days=1)
    if p in ("eow", "end of week", "end of the week"):
        return base + timedelta(days=(4 - base.weekday()) % 7)
    if p == "next week":
        return base + timedelta(days=7 - base.weekday())
    if p.startswith("next "):
        wd = _wd_index(p[5:])
        return base + timedelta(days=7 - base.weekday() + wd) if wd is not None else None
    if re.fullmatch(_WD_PAT, p):
        return base + timedelta(days=(_wd_index(p) - base.weekday()) % 7)
    m = re.fullmatch(r'(\d{1,2})[/-](\d{1,2})(?:[/-](\d{2,4}))?', p)
    if m:
        a, b, y = int(m.group(1)), int(m.group(2)), m.group(3)
        yr = base.year if not y else (int(y) + 2000 if len(y) == 2 else int(y))
        for d_, mo in ((a, b), (b, a)):     # day-first, then month-first if that is invalid
            try:
                return date(yr, mo, d_)
            except ValueError:
                continue
    return None


def fmt_short_date(d: date) -> str:
    return d.strftime("%a, %b %d")


def find_date_phrases(text: str):
    """[(phrase_as_written, phrase_to_resolve)] — bare weekdays / numeric dates need a preposition
    (by/before/on/due…) so 'Friday standup' or '3/4 done' are not mistaken for deadlines."""
    out = []
    for mt in _DATE_PHRASE_RE.finditer(text or ""):
        p, pre = mt.group("p"), mt.group("pre")
        bare_ok = re.fullmatch(r'(?i)tomorrow|today|tonight|eod|eow|cob|end of (?:the )?(?:day|week)|next week|next ' + _WD_PAT, p)
        if not pre and not bare_ok:
            continue
        out.append(((pre + " " if pre else "") + p, p))
    return out


def extract_dated_mentions(members: list, base: date) -> list:
    res = []
    for m in members:
        for t in m.get("tasks", []):
            for shown, p in find_date_phrases(t):
                d = resolve_date_phrase(p, base)
                if d:
                    res.append({"name": m["name"], "text": t, "phrase": shown, "date": d.isoformat()})
                    break
    return res


def resolve_action_dates(items: list, base: date) -> list:
    out = []
    for it in items:
        d = resolve_date_phrase(it.get("when", ""), base)
        out.append({**it, "date": d.isoformat() if d else ""})
    return out


# ── 22: consistency check (notes vs. generated output) ──
_STOP = frozenset("a an the and or of to in on for with at by from is are was were be been being it its this that these those as but not no we i you he she they them our their his her will would can could should may might do does did done has have had into over under about after before again up out so if then than also just only more most very all any each per via".split())
_BOILER_RE = re.compile(
    r"^(good morning|dear team|regards|kindly revert|that concludes|please find|here is the|subject:|daily (project )?status|hi\b|hello|thanks|thank you|"
    r"project team|blockers identified|no blockers|quick question|the following)", re.I)


def _stem(w: str) -> str:
    for suf in ("ing", "ed", "es", "s", "ly"):
        if len(w) > len(suf) + 3 and w.endswith(suf):
            return w[:-len(suf)]
    return w


def _stems(text: str) -> set:
    return {_stem(w) for w in re.findall(r"[a-z0-9']+", (text or "").lower()) if len(w) > 2 and w not in _STOP}


def _split_sentences(text: str) -> list:
    parts = []
    for line in (text or "").splitlines():
        line = line.strip().lstrip("-•*").strip().strip("*_")
        for s in re.split(r'(?<=[.!?])\s+', line):
            s = s.strip()
            if s:
                parts.append(s)
    return parts


def consistency_check(members: list, output_texts: list) -> dict:
    """Deterministic (no LLM): (1) tasks in the notes with no counterpart in the output, (2) output
    sentences with no source in the notes. Fuzzy: SequenceMatcher ratio OR content-word overlap."""
    sents = [s for t in output_texts for s in _split_sentences(t)]
    out_stems = set().union(*[_stems(s) for s in sents]) if sents else set()
    names = {m["name"].lower() for m in members}
    name_stems = set().union(*[_stems(n) for n in names]) if names else set()
    tasks = [(m["name"], t) for m in members for t in m.get("tasks", [])]
    src_stems = set().union(*[_stems(t) for _, t in tasks]) if tasks else set()
    missing = []
    for nm, t in tasks:
        cw = _stems(t) - name_stems
        if not cw:
            continue
        recall = len(cw & out_stems) / len(cw)
        best = max((_SM(None, t.lower(), s.lower()).ratio() for s in sents), default=0)
        if recall < 0.5 and best < 0.5:
            missing.append((nm, t))
    unsupported, seen = [], set()
    for s in sents:
        if len(s.split()) < 4 or _BOILER_RE.match(s) or s.lower().rstrip(":") in names or s in seen:
            continue
        cw = _stems(s) - name_stems
        if len(cw) < 2:
            continue
        prec = len(cw & src_stems) / len(cw)
        best = max((_SM(None, s.lower(), t.lower()).ratio() for _, t in tasks), default=0)
        if prec < 0.35 and best < 0.4:
            unsupported.append(s)
            seen.add(s)
    return {"missing": missing, "unsupported": unsupported, "tasks": len(tasks), "sentences": len(sents)}


# ── 37: input validation hints ──
_HEADER_LINE_RE = re.compile(r'^[A-Z][^\n:]{0,30}:')


def validate_input(raw: str, members: list, expect_blockers: bool = True) -> list:
    """Returns a list of short hint strings (all deterministic)."""
    hints = []
    if not (raw or "").strip():
        return hints
    cur = None
    cur_bullets = {}
    header_order = []
    for i, ln in enumerate(raw.splitlines(), 1):
        st_ = ln.strip()
        if not st_:
            continue
        if len(st_) > 300:
            hints.append(f"Line {i} is very long ({len(st_)} characters) — consider splitting it into bullets.")
        if st_[0] in "-•*":
            if cur is None:
                hints.append(f"Line {i} is a bullet but sits above any “Name:” header, so no member owns it.")
            else:
                cur_bullets[cur] = cur_bullets.get(cur, 0) + 1
        elif _HEADER_LINE_RE.match(st_):
            cur = st_.split(":")[0].strip()
            header_order.append(cur)
            cur_bullets.setdefault(cur, 0)
        else:
            if cur is None:
                hints.append(f"Line {i} (“{st_[:40]}”) isn't under a member — no “Name:” header was detected before it.")
            else:
                hints.append(f"Line {i} under {cur} isn't a bullet (start it with “- ”) and will be ignored.")
    for nm in header_order:
        if cur_bullets.get(nm, 0) == 0:
            hints.append(f"{nm} has no tasks listed — add at least one “- ” bullet or remove the header.")
    by_lower = {}
    for nm in header_order:
        by_lower.setdefault(nm.lower(), set()).add(nm)
    for variants in by_lower.values():
        if len(variants) > 1:
            hints.append("Duplicate names with different case: " + ", ".join(sorted(variants)) + " — they are treated as separate members.")
    if members and expect_blockers and not any(m.get("blockers") for m in members):
        hints.append("No blockers detected — if someone is stuck, phrase it with words like “blocked on”, “waiting for” or “need approval” so it is highlighted.")
    seen, out = set(), []
    for h in hints:
        if h not in seen:
            seen.add(h)
            out.append(h)
    return out[:8]


# ── 21 / 23: LLM wrappers (always behind their own buttons) ──
REVISE_OPTIONS = {
    "shorter":  ("Shorter",      "Make every field roughly 35-40% shorter. Keep every person, every task and every blocker; remove filler words and repetition only."),
    "formal":   ("More formal",  "Raise the register: formal, precise, professional wording. No slang, no contractions, no exclamation marks. Keep all facts."),
    "numbers":  ("Add numbers",  "Surface quantities. Where the text already states or clearly implies a count, percentage, duration or date, state it explicitly and prominently. NEVER invent a figure that is not in the input."),
    "friendly": ("Friendlier",   "Make the tone warm, upbeat and approachable while staying professional. Light touches only; keep all facts and structure."),
}


def revise_output(fields: dict, key: str, mask: bool = False):
    """Revise the CURRENT output (not the raw notes). Returns (new_fields, tokens, err)."""
    label, instr = REVISE_OPTIONS[key]
    payload = {k: v for k, v in fields.items() if isinstance(v, str) and v.strip()}
    if mask:
        payload = {k: mask_sensitive(v)[0] for k, v in payload.items()}
    sysmsg = (
        f"MODE: REVISE {label}\n"
        "You are SanghaStatus' editor. You receive a JSON object of already-written team status texts and an instruction. "
        "Rewrite EACH value according to the instruction. Keep the SAME JSON keys, the same language, the same people, "
        "the same line-break/bullet structure, headers, sign-offs and any footer lines. Do not add or drop people or tasks. "
        "Return ONLY the JSON object. No markdown fences, no reasoning, no <think> tags."
    )
    user = "CURRENT_OUTPUT_JSON:" + json.dumps(payload, ensure_ascii=False) + "\nINSTRUCTION: " + instr
    try:
        data, completion = call_llm_json(sysmsg, user, 0.2, min(3500, 900 + sum(len(v) for v in payload.values()) // 2))
    except Exception as e:
        return None, 0, str(e)[:200]
    out = {k: (data[k].strip() if isinstance(data.get(k), str) and data[k].strip() else fields[k]) for k in payload}
    if all(out[k] == payload[k] for k in out):
        return None, 0, "The model returned the text unchanged — try again."
    toks = completion.usage.total_tokens if getattr(completion, "usage", None) else 0
    return out, toks, ""


AUDIENCE_OPTIONS = {
    "manager": ("For my manager", "Write for a MANAGER: lead with outcomes and risks in 3-5 crisp lines, then who needs what from them. Mention blockers with owner and impact. No code-level detail."),
    "client":  ("For the client", "Write for an EXTERNAL CLIENT: positive, factual, progress-focused. OMIT internal blockers, internal tooling or environment problems, staffing issues, @mentions and any person's internal difficulties. If something is delayed, phrase it neutrally as an adjusted timeline without naming internal causes."),
    "team":    ("For the team", "Write for the TEAM: friendly, concrete, first-person-plural ('we'), include who is blocked and what help is needed, and what is next."),
}


def audience_rewrite(kind: str, narrative: str, blocker_texts: list, mask: bool = False):
    """One LLM call → audience-specific text. Returns (text, tokens, err)."""
    label, instr = AUDIENCE_OPTIONS[kind]
    src = mask_sensitive(narrative)[0] if mask else narrative
    sysmsg = (
        f"MODE: AUDIENCE {label}\n"
        "You rewrite a finished team status update for a specific audience. Use ONLY facts present in the input; never invent work. "
        f"{instr}\nReturn ONLY a JSON object {{\"text\": \"...\"}}. No markdown fences, no reasoning, no <think> tags."
    )
    try:
        data, completion = call_llm_json(sysmsg, "STATUS_UPDATE:\n" + src, 0.2, 1400)
    except Exception as e:
        return "", 0, str(e)[:200]
    text = str(data.get("text", "")).strip()
    if not text:
        return "", 0, "Empty response — try again."
    if kind == "client":
        text = scrub_for_client(text, blocker_texts)
    toks = completion.usage.total_tokens if getattr(completion, "usage", None) else 0
    return text, toks, ""


def scrub_for_client(text: str, blocker_texts: list) -> str:
    """Deterministic safety net on top of the prompt: drop @mentions and any sentence that repeats an
    internal blocker from the notes."""
    text = re.sub(r'@[A-Za-z][\w]{1,30}', '', text)
    kept = []
    for line in text.splitlines():
        ok = []
        for s in re.split(r'(?<=[.!?])\s+', line):
            low = s.lower()
            hit = any(
                b and (_SM(None, low, b.lower()).ratio() > 0.55 or (len(_stems(b)) >= 3 and len(_stems(s) & _stems(b)) / len(_stems(b)) >= 0.6))
                for b in blocker_texts
            ) or bool(re.search(r'\b(blocked|blocker|waiting (?:on|for)|stuck)\b', low))
            if not hit:
                ok.append(s)
        kept.append(" ".join(ok).replace("  ", " ").strip())
    return re.sub(r'\n{3,}', '\n\n', "\n".join(kept)).strip()


# ═══════════════════════════════════════════════════════════════════
# ITERATION B HELPERS — team workflow & output.
# ═══════════════════════════════════════════════════════════════════
import copy as _copy
import io as _io
import base64 as _b64

# ── 30: templates beyond standup. JSON keys stay the same so every renderer/export keeps working;
# only the prompt instructions and the display labels change. "Standup" adds NOTHING to the prompts
# (byte-for-byte the previous behaviour). ──
TEMPLATES = {
    "Standup":         {"title": "Daily Status Update",  "narr_title": "Standup Narrative", "tab_narrative": "Narrative",
                        "tab_tomorrow": "Tomorrow", "tab_blockers": "Blockers", "tomorrow_title": "Tomorrow's Plan", "blockers_title": "Blockers"},
    "Release notes":   {"title": "Release Notes",        "narr_title": "Release Notes",     "tab_narrative": "Release notes",
                        "tab_tomorrow": "Next release", "tab_blockers": "Known issues", "tomorrow_title": "Next Release", "blockers_title": "Known Issues"},
    "Incident update": {"title": "Incident Update",      "narr_title": "Incident Summary",  "tab_narrative": "Incident summary",
                        "tab_tomorrow": "Next actions", "tab_blockers": "Open risks", "tomorrow_title": "Next Actions", "blockers_title": "Open Risks"},
    "Weekly status":   {"title": "Weekly Status Report", "narr_title": "Weekly Summary",    "tab_narrative": "Weekly summary",
                        "tab_tomorrow": "Next week", "tab_blockers": "Risks & blockers", "tomorrow_title": "Plan for Next Week", "blockers_title": "Risks & Blockers"},
}
_TEMPLATE_GUIDE = {
    "Release notes": (
        "RELEASE NOTES",
        "Group the raw items under short headings that apply — \"New\", \"Improved\", \"Fixed\" — as bullets in user-facing language. "
        "Credit the person in brackets after each bullet, e.g. \"(Alice)\". No greeting and no 'status update' framing. "
        "tomorrow_plan (if requested) = what is planned for the NEXT release; blocker_summary (if requested) = KNOWN ISSUES."),
    "Incident update": (
        "INCIDENT UPDATE",
        "Structure it as: Impact, Current status, Actions taken (who did what), Next steps and next update time (only if the notes give one). "
        "Calm, factual, timestamped wording when the notes include times. tomorrow_plan (if requested) = NEXT ACTIONS; "
        "blocker_summary (if requested) = OPEN RISKS / what is still unresolved."),
    "Weekly status": (
        "WEEKLY STATUS REPORT",
        "Write it as a weekly report: Highlights, Progress by person, Risks, Next week. Summarise themes instead of repeating every sentence verbatim, "
        "but still mention every person. tomorrow_plan (if requested) = PLAN FOR NEXT WEEK; blocker_summary (if requested) = RISKS & BLOCKERS."),
}


def template_prompt_block(template: str, kind: str) -> str:
    """'' for Standup (unchanged prompts). For other templates, an override block appended to the prompt."""
    if template not in _TEMPLATE_GUIDE:
        return ""
    name, guide = _TEMPLATE_GUIDE[template]
    t = TEMPLATES[template]
    head = {"narrative": "standup_narrative", "chat": "chat_update / whatsapp_update", "email": "email_update"}[kind]
    return (
        f"\nTEMPLATE OVERRIDE — {name}: this is NOT a daily standup. Keep the JSON keys EXACTLY as specified above, "
        f"but write the value of {head} as a {t['title'].lower()}. {guide} "
        f"Replace phrases like 'Daily Status Update' / 'status update' in headers and subject lines with '{t['title']}'. "
        "Still use ONLY facts from the raw input, rewrite every item as a full sentence, and keep each person's items attributed.\n"
    )


# ── 27: blocker owner + needs-by ──
def _bk_key(name: str, text: str) -> str:
    return hashlib.md5(f"{name}|{text}".encode()).hexdigest()[:8]


def _resolve_due(text: str, base: date):
    text = (text or "").strip()
    if not text:
        return ""
    d = resolve_date_phrase(text.lower().replace("by ", "").strip(), base)
    if d is None:
        try:
            d = datetime.fromisoformat(text).date()
        except Exception:
            d = None
    return d.isoformat() if d else ""


def _collect_blocker_meta(members: list, base: date) -> list:
    out = []
    for m in members:
        for b in m.get("blockers", []):
            k = _bk_key(m["name"], b)
            owner = str(st.session_state.get(f"bk_owner_{k}", "") or "").strip()
            due = str(st.session_state.get(f"bk_due_{k}", "") or "").strip()
            if owner or due:
                out.append({"name": m["name"], "blocker": b, "owner": owner, "needs_by": due, "needs_by_date": _resolve_due(due, base)})
    return out


def blocker_meta_prompt(meta: list) -> str:
    if not meta:
        return ""
    lines = "\n".join(
        f"- {x['name']}: \"{x['blocker']}\" -> owner: {x['owner'] or 'unassigned'}; needed by: {x['needs_by_date'] or x['needs_by'] or 'not set'}"
        for x in meta)
    return ("\nBlocker owners and needed-by dates (state the owner and the needed-by date in the blocker details for these, "
            "verbatim, and in the person's bullet where natural):\n" + lines + "\n")


# ── 26: yesterday -> today prefill ──
_DONE_RE = re.compile(r'\b(done|completed?|finished|deployed|fixed|merged|resolved|shipped|released|delivered|closed|signed off|wrapped up|submitted)\b', re.I)


def build_prefill_text(history: list) -> str:
    """Yesterday's still-open tasks + unresolved blockers per member. Follow-through logic: a task counts as
    open unless it is phrased as completed; blockers and 'will … by …' action items always carry over."""
    if not history:
        return ""
    blocks = []
    for m in history[0].get("members_detail", []):
        keep = [t for t in m.get("tasks", [])
                if t in m.get("blockers", []) or ACTION_ITEM_RE.search(t) or not _DONE_RE.search(t)]
        if keep:
            blocks.append(f"{m['name']}:\n" + "\n".join(f"- {t}" for t in keep))
    return "\n\n".join(blocks)


# ── 29: sprint goal tracker (SQLite, keyed by TEAM_SLUG) ──
def load_sprint_goal() -> str:
    try:
        raw = _kv_get_raw("sprint_goal", TEAM_SLUG)
        return json.loads(raw).get("goal", "") if raw else ""
    except Exception:
        return ""


def save_sprint_goal(goal: str) -> None:
    try:
        _kv_set_raw("sprint_goal", TEAM_SLUG, {"goal": goal})
    except Exception:
        pass


def map_tasks_to_goal(goal: str, members: list) -> dict:
    kw = _stems(goal)
    linked, unlinked = [], []
    for m in members:
        for t in m.get("tasks", []):
            (linked if (kw & _stems(t)) else unlinked).append((m["name"], t))
    total = len(linked) + len(unlinked)
    return {"linked": linked, "unlinked": unlinked, "pct": round(100 * len(linked) / total) if total else 0, "keywords": sorted(kw)}


# ── 32: team logo (SQLite blob per team) ──
def _logo_conn():
    conn = _get_db_conn()
    conn.execute("CREATE TABLE IF NOT EXISTS team_logo (team_slug TEXT PRIMARY KEY, mime TEXT, data BLOB)")
    return conn


def load_logo():
    try:
        conn = _logo_conn()
        row = conn.execute("SELECT mime, data FROM team_logo WHERE team_slug=?", (TEAM_SLUG,)).fetchone()
        conn.close()
        return (row[0], bytes(row[1])) if row else None
    except Exception:
        return None


def save_logo(mime: str, data: bytes) -> None:
    try:
        conn = _logo_conn()
        conn.execute("INSERT INTO team_logo (team_slug, mime, data) VALUES (?,?,?) ON CONFLICT(team_slug) DO UPDATE SET mime=excluded.mime, data=excluded.data",
                     (TEAM_SLUG, mime, data))
        conn.commit()
        conn.close()
    except Exception:
        pass


def delete_logo() -> None:
    try:
        conn = _logo_conn()
        conn.execute("DELETE FROM team_logo WHERE team_slug=?", (TEAM_SLUG,))
        conn.commit()
        conn.close()
    except Exception:
        pass


def validate_logo(name: str, data: bytes):
    """png/jpg <= 1 MB that Pillow can actually open. Returns (mime, err)."""
    if len(data) > 1_000_000:
        return None, "Logo must be 1 MB or smaller."
    try:
        from PIL import Image
        im = Image.open(_io.BytesIO(data))
        fmt = (im.format or "").upper()
        im.verify()
    except Exception:
        return None, "That file isn't a readable PNG/JPG image."
    if fmt not in ("PNG", "JPEG"):
        return None, "Only PNG or JPG logos are supported."
    return ("image/png" if fmt == "PNG" else "image/jpeg"), ""


# ── 36: output versions ──
def _make_version_snapshot(res: dict, label: str) -> dict:
    n = res.get("_vn", 0) + 1
    res["_vn"] = n
    return {"n": n, "label": label, "ts": datetime.now().strftime("%H:%M:%S"), "data": _copy.deepcopy(res["data"]),
            "narrative": res["narrative"], "chat": res["chat"], "wa": res["wa"], "email_raw": res["email_raw"]}


def _apply_snapshot(res: dict, snap: dict) -> None:
    res["data"] = _copy.deepcopy(snap["data"])
    for k in ("narrative", "chat", "wa", "email_raw"):
        res[k] = snap[k]
    res["refresh_edits"] = True


def _persist_output_to_history(res: dict) -> None:
    h = st.session_state.history
    if h and res.get("saved_at") and h[0].get("saved_at") == res["saved_at"]:
        h[0]["data"] = _copy.deepcopy(res["data"])
        save_history_to_disk(h)


# ── 31: markdown + HTML export, 33: Confluence/Notion clipboard ──
def current_texts(res: dict) -> dict:
    """Current (possibly hand-edited) texts of the stored output."""
    g = st.session_state.get
    d = res["data"]
    return {
        "narrative": g("edit_narrative", res["narrative"]), "chat": g("edit_chat", res["chat"]),
        "wa": g("edit_whatsapp", res["wa"]), "email": g("edit_email", res["email_raw"]),
        "tomorrow": d.get("tomorrow_plan", "") if res.get("include_tomorrow") else "",
        "blockers": d.get("blocker_summary", "") if res.get("include_blockers") else "",
    }


def _meta_rows(res: dict):
    return [(x["name"], x["blocker"], x.get("owner") or "—", x.get("needs_by_date") or x.get("needs_by") or "—")
            for x in (res.get("blocker_meta") or [])]


def build_markdown_export(res: dict) -> str:
    t = current_texts(res)
    tpl = TEMPLATES.get(res.get("template", "Standup"), TEMPLATES["Standup"])
    out = [f"# {tpl['title']} — {res['fmt_date']}"]
    sub = " · ".join(x for x in [f"Project: {res['project']}" if res.get("project") else "", f"Prepared by {res['prepared_by']}" if res.get("prepared_by") else ""] if x)
    if sub:
        out.append(f"_{sub}_")
    if res.get("metrics"):
        out.append("**By the numbers:** " + " · ".join(f"{n} {l}" for l, n in res["metrics"]))
    out += [f"\n## {tpl['narr_title']}\n", t["narrative"]]
    if t["tomorrow"]:
        out += [f"\n## {tpl['tomorrow_title']}\n", t["tomorrow"]]
    if t["blockers"] or res.get("blocker_meta"):
        out += [f"\n## {tpl['blockers_title']}\n", t["blockers"]]
        rows = _meta_rows(res)
        if rows:
            out += ["", "| Person | Blocker | Owner | Needed by |", "|---|---|---|---|"] + [f"| {a} | {b} | {c} | {d} |" for a, b, c, d in rows]
    out += ["\n## Chat Update\n", t["chat"], "\n## Email Update\n", t["email"]]
    return "\n".join(out).strip() + "\n"


def simple_md_to_html(md: str) -> str:
    """Tiny markdown subset (headings, bullets, tables, bold/italic, paragraphs) -> HTML fragment. Used for the
    HTML export and the formatted clipboard copy (Confluence/Notion accept pasted rich text)."""
    def inline(s):
        s = _html.escape(s)
        s = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', s)
        s = re.sub(r'(?<![\w*])_(.+?)_(?![\w*])', r'<em>\1</em>', s)
        return s
    out, in_ul, in_tbl = [], False, False
    for ln in md.splitlines():
        st_ = ln.rstrip()
        is_li = bool(re.match(r'\s*[-•*]\s+', st_))
        if in_ul and not is_li:
            out.append("</ul>"); in_ul = False
        if in_tbl and not st_.startswith("|"):
            out.append("</table>"); in_tbl = False
        if not st_.strip():
            continue
        m = re.match(r'(#{1,3})\s+(.*)', st_)
        if m:
            lv = len(m.group(1)); out.append(f"<h{lv}>{inline(m.group(2))}</h{lv}>")
        elif st_.startswith("|"):
            if re.fullmatch(r'\|[\s|:-]+\|', st_):
                continue
            cells = [c.strip() for c in st_.strip("|").split("|")]
            if not in_tbl:
                out.append('<table border="1" cellpadding="6" style="border-collapse:collapse">'); in_tbl = True
                out.append("<tr>" + "".join(f"<th>{inline(c)}</th>" for c in cells) + "</tr>")
            else:
                out.append("<tr>" + "".join(f"<td>{inline(c)}</td>" for c in cells) + "</tr>")
        elif is_li:
            if not in_ul:
                out.append("<ul>"); in_ul = True
            _li = re.sub(r'^\s*[-\u2022*]\s+', '', st_)
            out.append("<li>" + inline(_li) + "</li>")
        else:
            out.append(f"<p>{inline(st_)}</p>")
    if in_ul:
        out.append("</ul>")
    if in_tbl:
        out.append("</table>")
    return "\n".join(out)


def build_html_export(res: dict) -> str:
    tpl = TEMPLATES.get(res.get("template", "Standup"), TEMPLATES["Standup"])
    body = simple_md_to_html(build_markdown_export(res))
    css = ("body{font:16px/1.6 -apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;max-width:760px;margin:2rem auto;padding:0 1rem;color:#1d1d1f;background:#fff}"
           "h1{font-size:1.7rem;border-bottom:2px solid #b5532f;padding-bottom:.4rem}h2{font-size:1.2rem;margin-top:2rem;color:#8f3416}"
           "p{margin:.4rem 0;white-space:pre-wrap}ul{padding-left:1.2rem}table{margin:.6rem 0;font-size:.9rem}th{background:#f2f2f4;text-align:left}"
           "@media (prefers-color-scheme:dark){body{background:#111;color:#f5f5f7}h2{color:#f0956f}th{background:#2c2c2e}}")
    return (f'<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
            f'<title>{_html.escape(tpl["title"])} — {_html.escape(res["fmt_date"])}</title><style>{css}</style></head><body>{body}</body></html>')


# ── 28: weekly summary (deterministic stats + optional LLM paragraph) ──
def _entry_date(e: dict):
    try:
        return datetime.strptime(e.get("date", ""), "%B %d, %Y").date()
    except Exception:
        try:
            return datetime.fromisoformat(e.get("saved_at", "")).date()
        except Exception:
            return None


@st.cache_data(show_spinner=False, max_entries=16)
def week_stats(history_json: str, today_iso: str, goal: str = "") -> dict:
    history = json.loads(history_json)
    today = date.fromisoformat(today_iso)
    cutoff = today - timedelta(days=6)
    ents = [(e, _entry_date(e)) for e in history]
    ents = [(e, d) for e, d in ents if d and cutoff <= d <= today]
    per_member, blockers, health = {}, {}, []
    tasks = nb = 0
    for e, _d in ents:
        md = e.get("members_detail", [])
        tasks += sum(len(m.get("tasks", [])) for m in md)
        for m in md:
            per_member[m["name"]] = per_member.get(m["name"], 0) + len(m.get("tasks", []))
            for b in m.get("blockers", []):
                nb += 1
                blockers[(m["name"], b)] = blockers.get((m["name"], b), 0) + 1
        health.append(compute_health_score(md, {}, {})[0])
    top = sorted(blockers.items(), key=lambda kv: -kv[1])[:5]
    goal_pct = None
    if goal and ents:
        latest = max(ents, key=lambda x: x[1])[0]
        goal_pct = map_tasks_to_goal(goal, latest.get("members_detail", []))["pct"]
    return {"from": cutoff.isoformat(), "to": today.isoformat(), "standups": len(ents), "tasks": tasks, "blockers": nb,
            "per_member": sorted(per_member.items(), key=lambda kv: -kv[1]), "top_blockers": [(a, b, n) for (a, b), n in top],
            "health_avg": round(sum(health) / len(health)) if health else None, "goal_pct": goal_pct,
            "metrics": [], "friday": today.weekday() == 4}


def week_text(w: dict) -> str:
    if not w["standups"]:
        return "No standups saved in the last 7 days."
    lines = [f"WEEKLY ROLL-UP · {w['from']} to {w['to']}", "",
             f"Standups: {w['standups']}  ·  Tasks reported: {w['tasks']}  ·  Blockers raised: {w['blockers']}"
             + (f"  ·  Avg health: {w['health_avg']}" if w["health_avg"] is not None else "")]
    if w.get("goal_pct") is not None:
        lines.append(f"Sprint goal alignment (latest standup): {w['goal_pct']}% of tasks linked")
    lines += ["", "Tasks by person:"] + [f"- {n}: {c}" for n, c in w["per_member"]]
    if w["top_blockers"]:
        lines += ["", "Most persistent blockers:"] + [f"- {a}: {b} (seen {n}x)" for a, b, n in w["top_blockers"]]
    return "\n".join(lines)


def week_llm_paragraph(text: str, mask: bool = False):
    src = mask_sensitive(text)[0] if mask else text
    sysmsg = ("MODE: WEEKPARA\nYou write one short, factual paragraph (3-4 sentences) summarising a team's week from the statistics given. "
              "Use only the numbers and names provided. Return ONLY JSON {\"paragraph\": \"...\"}. No fences, no <think> tags.")
    try:
        data, completion = call_llm_json(sysmsg, "WEEK_STATS:\n" + src, 0.2, 500)
    except Exception as e:
        return "", 0, str(e)[:200]
    para = str(data.get("paragraph", "")).strip()
    return para, (completion.usage.total_tokens if getattr(completion, "usage", None) else 0), ("" if para else "Empty response.")


# ── 38: backup & restore (current team; never the PIN hash) ──
BACKUP_SCHEMA = 1


def build_backup() -> dict:
    logo = load_logo()
    return {
        "app": "SanghaStatus", "schema_version": BACKUP_SCHEMA, "team": TEAM_SLUG,
        "exported_at": datetime.now().isoformat(timespec="seconds"),
        "roster": load_roster(), "presets": load_presets(), "glossary": load_glossary(),
        "history": st.session_state.history, "sprint_goal": load_sprint_goal(),
        "logo": ({"mime": logo[0], "b64": _b64.b64encode(logo[1]).decode()} if logo else None),
    }


def validate_backup(obj) -> tuple:
    """(ok, message). Checks app marker, schema version and basic types — nothing is written here."""
    if not isinstance(obj, dict) or obj.get("app") != "SanghaStatus":
        return False, "This isn't a SanghaStatus backup file."
    v = obj.get("schema_version")
    if not isinstance(v, int) or v > BACKUP_SCHEMA or v < 1:
        return False, f"Unsupported backup schema version ({v!r}); this app understands up to {BACKUP_SCHEMA}."
    if not isinstance(obj.get("roster", {}), dict) or not isinstance(obj.get("presets", {}), dict) \
            or not isinstance(obj.get("glossary", []), list) or not isinstance(obj.get("history", []), list):
        return False, "The backup is damaged (unexpected data types)."
    for e in obj.get("history", []):
        if not isinstance(e, dict) or "data" not in e or "members_detail" not in e:
            return False, "The backup's history entries are damaged."
    return True, "ok"


def apply_backup(obj: dict) -> None:
    save_roster(obj.get("roster", {}))
    save_presets(obj.get("presets", {}))
    save_glossary(obj.get("glossary", []))
    hist = obj.get("history", [])[:MAX_HISTORY]
    st.session_state.history = hist
    save_history_to_disk(hist)
    save_sprint_goal(obj.get("sprint_goal", "") or "")
    lg = obj.get("logo")
    if lg and lg.get("b64"):
        try:
            save_logo(lg.get("mime", "image/png"), _b64.b64decode(lg["b64"]))
        except Exception:
            pass
    else:
        delete_logo()


# ── 45: what's stored + reset ──
def stored_data_summary() -> list:
    rows = []
    try:
        conn = _get_db_conn()
        rows.append(("history entries", conn.execute("SELECT COUNT(*) FROM history").fetchone()[0], DB_FILE))
        for tbl, label in (("roster", "roster profile"), ("presets", "presets"), ("glossary", "glossary"), ("sprint_goal", "sprint goal"), ("ui_prefs", "interface preferences")):
            try:
                r = conn.execute(f"SELECT value_json FROM {tbl} WHERE team_slug=?", (TEAM_SLUG,)).fetchone()
                n = 0
                if r:
                    v = json.loads(r[0])
                    n = len(v) if isinstance(v, (list, dict)) and tbl not in ("sprint_goal", "ui_prefs") else 1
                rows.append((label, n, tbl))
            except Exception:
                rows.append((label, 0, tbl))
        try:
            r = conn.execute("SELECT LENGTH(data) FROM team_logo WHERE team_slug=?", (TEAM_SLUG,)).fetchone()
            rows.append(("logo (bytes)", r[0] if r else 0, "team_logo"))
        except Exception:
            rows.append(("logo (bytes)", 0, "team_logo"))
        conn.close()
    except Exception:
        pass
    rows.append(("team PIN", "set" if _get_team_pin_hash() else "not set", "hash never shown"))
    return rows


_RESET_PREF_KEYS = ("pref_tone", "pref_domain", "pref_lang", "pref_tomorrow", "pref_blockers", "pref_project", "pref_date",
                    "pref_ui_lang", "pref_contrast", "pref_template", "pref_brand_project", "scrub_mask", "member_view_mode")


def reset_team_preferences() -> None:
    for k in _RESET_PREF_KEYS:
        st.session_state.pop(k, None)
    try:
        conn = _get_db_conn()
        conn.execute("CREATE TABLE IF NOT EXISTS ui_prefs (team_slug TEXT PRIMARY KEY, value_json TEXT)")
        conn.execute("DELETE FROM ui_prefs WHERE team_slug=?", (TEAM_SLUG,))
        conn.commit()
        conn.close()
    except Exception:
        pass


# ── cached wrappers for the heavy-ish pure analytics (43) ──
@st.cache_data(show_spinner=False, max_entries=32)
def _c_analytics(members_json: str, history_json: str, out_json: str):
    members, history, out = json.loads(members_json), json.loads(history_json), json.loads(out_json)
    active = [m for m in members if m["name"] not in out]
    brief = flag_brief_updates(active, history)
    esc = flag_recurring_blockers(active, history)
    over = flag_overload_trend(active, history)
    score, label = compute_health_score(active, brief, esc)
    diffs = diff_against_previous(members, history[0]) if history else {}
    return {"brief": brief, "esc": esc, "over": over, "score": score, "label": label, "diffs": diffs}



# Command palette (Cmd/Ctrl+K) — same mechanism as SatiCast's: finds real
# elements in the parent document and clicks them, best-effort.
_JS_PALETTE = """
<script>
try {
  const doc = window.parent.document;
  if (!doc.getElementById('sanghaCmdPalette')) {
    const overlay = doc.createElement('div');
    overlay.id = 'sanghaCmdPalette';
    overlay.style.cssText = 'display:none;position:fixed;inset:0;z-index:999998;'
      + 'background:rgba(0,0,0,0.35);-webkit-backdrop-filter:blur(8px);backdrop-filter:blur(8px);align-items:flex-start;justify-content:center;padding-top:12vh;';
    overlay.innerHTML = `
      <div style="background:var(--card,#fff);color:var(--txt,#1d1d1f);border:1px solid var(--hair,rgba(0,0,0,.08));border-radius:22px;padding:0.6rem;width:min(420px,90vw);
                  box-shadow:0 24px 60px rgba(0,0,0,0.3);font-family:-apple-system,BlinkMacSystemFont,'SF Pro Text',Inter,'Segoe UI',Roboto,sans-serif;">
        <div style="padding:0.5rem 0.7rem;font-size:0.7rem;font-weight:700;letter-spacing:0.05em;
                    text-transform:uppercase;opacity:0.55;">Quick Actions &nbsp;·&nbsp; Esc to close</div>
        <button data-cmd="generate" class="sangha-cmd-item">Generate Professional Status</button>
        <button data-cmd="darkmode" class="sangha-cmd-item">Toggle dark mode</button>
        <button data-cmd="top" class="sangha-cmd-item">Scroll to top</button>
      </div>`;
    doc.body.appendChild(overlay);
    const style = doc.createElement('style');
    style.textContent = '.sangha-cmd-item { display:block; width:100%; text-align:left; padding:0.7rem 0.8rem; '
      + 'border:none; background:transparent; border-radius:12px; cursor:pointer; font-size:0.95rem; font-family:inherit; '
      + 'color:inherit; margin-bottom:2px; transition:background 0.18s; } .sangha-cmd-item:hover { background:rgba(201,100,66,0.14); }';
    doc.head.appendChild(style);

    function closePalette() { overlay.style.display = 'none'; }
    function openPalette() { overlay.style.display = 'flex'; }
    overlay.addEventListener('click', (e) => { if (e.target === overlay) closePalette(); });

    overlay.querySelectorAll('.sangha-cmd-item').forEach(btn => {
      btn.addEventListener('click', () => {
        const cmd = btn.dataset.cmd;
        if (cmd === 'darkmode') {
          const cb = doc.getElementById('dmchk');
          if (cb) cb.click();
        } else if (cmd === 'top') {
          (doc.scrollingElement || doc.documentElement).scrollTo({ top: 0, behavior: 'smooth' });
        } else if (cmd === 'generate') {
          const target = doc.querySelector('.st-key-generate_btn button');
          if (target) target.click();
        }
        closePalette();
      });
    });

    doc.defaultView.addEventListener('keydown', (e) => {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 'k') {
        e.preventDefault();
        overlay.style.display === 'flex' ? closePalette() : openPalette();
      } else if (e.key === 'Escape') {
        closePalette();
      }
    });
  }
} catch (e) {}
</script>
"""

# Theme sync — the CSS toggle (#dmchk) stays the single source of truth. On load we
# apply the person's explicit saved choice if there is one, otherwise the OS preference
# (prefers-color-scheme, also handled in pure CSS as a no-JS fallback), and we keep the
# <meta name="theme-color"> in step. Toggling in EITHER direction is remembered.
_JS_THEME = """
<script>
try {
  const w = window.parent, doc = w.document;
  const cb = doc.getElementById('dmchk');
  let meta = doc.querySelector('meta[name="theme-color"]');
  if (!meta) { meta = doc.createElement('meta'); meta.name = 'theme-color'; doc.head.appendChild(meta); }
  const paint = () => { meta.content = (cb && cb.checked) ? '#000000' : '#fbfbfd'; };
  if (cb) {
    const KEY = 'sanghastatus_theme';
    let saved = null;
    try { saved = w.localStorage.getItem(KEY); } catch (e) {}
    const prefersDark = !!(w.matchMedia && w.matchMedia('(prefers-color-scheme: dark)').matches);
    const want = saved ? (saved === 'dark') : prefersDark;
    if (saved) doc.documentElement.setAttribute('data-sangha-theme', saved);
    if (cb.checked !== want) { cb.click(); }
    paint();
    if (!cb.dataset.sanghaListenerBound) {
      cb.dataset.sanghaListenerBound = "1";
      cb.addEventListener('change', () => {
        const v = cb.checked ? 'dark' : 'light';
        try { w.localStorage.setItem(KEY, v); } catch (e) {}
        doc.documentElement.setAttribute('data-sangha-theme', v);
        paint();
      });
    }
  }
} catch (e) {}
</script>
"""

# ── 39 / 40 / 42: keyboard shortcuts, aria fixes, PWA bits — ONE zero-height iframe for all page scripts.
# The listeners are installed from a <script> element created IN the parent document so they outlive the iframe
# (Streamlit replaces the iframe on rerun). Everything is wrapped in try/catch: cross-frame access can fail.
# PWA note: Streamlit serves its own page, so a real offline install (service worker, start_url) is NOT possible
# here; the manifest / apple-touch-icon / theme-color / mobile-web-app-capable tags below are best-effort polish
# that make "Add to Home Screen" look right on phones.
import functools as _functools


@_functools.lru_cache(maxsize=1)
def _pwa_icon_b64() -> str:
    try:
        from PIL import Image, ImageDraw
        im = Image.new("RGB", (180, 180), (181, 83, 47))
        d = ImageDraw.Draw(im)
        for x in (48, 74, 100, 126):                      # little "temple" columns, echoing the topbar logo
            d.rectangle([x, 80, x + 12, 138], fill=(255, 255, 255))
        d.polygon([(34, 80), (90, 44), (146, 80)], fill=(255, 255, 255))
        d.rectangle([34, 142, 146, 150], fill=(255, 255, 255))
        buf = _io.BytesIO()
        im.save(buf, "PNG")
        return _b64.b64encode(buf.getvalue()).decode()
    except Exception:
        return ""


_JS_KEYS_TEMPLATE = r"""
<script>
try {
  const w = window.parent, doc = w.document;
  if (!w.__sanghaKeysInstalled) {
    w.__sanghaKeysInstalled = true;
    const code = `(function(){
      var doc = document;
      function typing(e){ var t=e.target; if(!t||!t.tagName) return false; var n=t.tagName.toLowerCase();
        return n==='input'||n==='textarea'||n==='select'||t.isContentEditable||(t.getAttribute&&t.getAttribute('role')==='combobox'); }
      function live(msg){ var l=doc.getElementById('sangha-live'); if(!l){ l=doc.createElement('div'); l.id='sangha-live'; l.className='sr-only';
        l.setAttribute('aria-live','polite'); l.setAttribute('role','status'); doc.body.appendChild(l);} l.textContent=''; setTimeout(function(){ l.textContent=msg; },60); }
      function toast(html, plain){ var el=doc.getElementById('sangha-toast'); if(!el){ el=doc.createElement('div'); el.id='sangha-toast'; el.setAttribute('role','status'); doc.body.appendChild(el);}
        el.innerHTML=html; el.style.display='block'; clearTimeout(el._t); el._t=setTimeout(function(){ el.style.display='none'; }, 7000); live(plain); }
      doc.addEventListener('keydown', function(e){
        try {
          if ((e.ctrlKey||e.metaKey) && e.key==='Enter') {
            var b = doc.querySelector('.st-key-generate_btn button');
            if (b) { e.preventDefault(); setTimeout(function(){ b.click(); }, typing(e)?350:0); }
            return;
          }
          if (e.ctrlKey||e.metaKey||e.altKey||typing(e)) return;
          if (e.key==='/') { var ta = doc.querySelector('.st-key-raw_input textarea') || doc.querySelector('[data-testid="stTextArea"] textarea'); if (ta) { e.preventDefault(); ta.focus(); live('Notes box focused'); } }
          else if (e.key==='d'||e.key==='D') { var cb = doc.getElementById('dmchk'); if (cb) { cb.click(); live(cb.checked ? 'Dark mode on' : 'Dark mode off'); } }
          else if (e.key==='?') { toast('<b>Shortcuts</b><br><kbd>Ctrl</kbd>+<kbd>Enter</kbd> Generate &nbsp; <kbd>/</kbd> Focus notes<br><kbd>D</kbd> Toggle dark mode &nbsp; <kbd>Ctrl</kbd>+<kbd>K</kbd> Quick actions<br><kbd>?</kbd> This help', 'Shortcuts: Control Enter generates, slash focuses notes, D toggles dark mode, question mark shows help'); }
        } catch (err) {}
      }, true);
      doc.addEventListener('click', function(e){ try { var t = e.target.closest && e.target.closest('[role="tab"]'); if (t) live('Tab ' + (t.textContent||'').trim() + ' selected'); } catch (err) {} }, true);
      var pending = null;
      function fixAria(){ try {
        doc.querySelectorAll('button:not([aria-label])').forEach(function(b){
          var t=(b.textContent||'').trim();
          if (!/[A-Za-z0-9ऀ-ॿ]/.test(t)) { var lbl = b.getAttribute('title') || ((t.indexOf('🗑')>-1) ? 'Delete' : (b.getAttribute('data-testid')||'').replace(/^stBase?Button-?/,'') || 'Action'); b.setAttribute('aria-label', lbl); } });
        doc.querySelectorAll('[data-testid="stToast"],[data-baseweb="toast"]').forEach(function(x){ if(!x.getAttribute('role')) x.setAttribute('role','status'); });
      } catch (err) {} }
      new MutationObserver(function(){ clearTimeout(pending); pending = setTimeout(fixAria, 500); }).observe(doc.body, {childList:true, subtree:true});
      fixAria();
    })();`;
    const s = doc.createElement('script'); s.textContent = code; doc.head.appendChild(s);
  }
  // PWA bits (best-effort; see the Python comment for the offline-install limitation)
  function ensureMeta(name, content){ var m = doc.querySelector('meta[name="'+name+'"]'); if(!m){ m = doc.createElement('meta'); m.name = name; doc.head.appendChild(m);} m.content = content; }
  ensureMeta('mobile-web-app-capable', 'yes'); ensureMeta('apple-mobile-web-app-capable', 'yes');
  ensureMeta('apple-mobile-web-app-title', 'SanghaStatus'); ensureMeta('application-name', 'SanghaStatus');
  var ICON = "__ICON__";
  if (ICON && !doc.querySelector('link[rel="apple-touch-icon"]')) {
    var l = doc.createElement('link'); l.rel = 'apple-touch-icon'; l.href = 'data:image/png;base64,' + ICON; doc.head.appendChild(l);
    if (!doc.querySelector('link[rel="manifest"][data-sangha]')) {
      var man = {name:'SanghaStatus', short_name:'Sangha', display:'standalone', start_url:'.', background_color:'#fbfbfd', theme_color:'#b5532f',
                 icons:[{src:'data:image/png;base64,' + ICON, sizes:'180x180', type:'image/png'}]};
      var ml = doc.createElement('link'); ml.rel = 'manifest'; ml.setAttribute('data-sangha','1');
      ml.href = 'data:application/manifest+json;base64,' + btoa(JSON.stringify(man)); doc.head.appendChild(ml);
    }
  }
} catch (e) {}
</script>
"""

components.html(_JS_PALETTE + _JS_THEME + _JS_KEYS_TEMPLATE.replace("__ICON__", _pwa_icon_b64()), height=0, width=0)

# ═══════════════════════════════════════════════════
# CADENCE REMINDER — session-visible only, no push notifications. Flags
# when it's been notably longer than usual since the last saved standup
# for this team, using a threshold that adapts to the team's own recent
# cadence (falls back to a flat 24h once at least 2 past gaps are known).
# ═══════════════════════════════════════════════════
if st.session_state.history:
    _hist_with_ts = [e for e in st.session_state.history if e.get("saved_at")]
    if _hist_with_ts:
        try:
            _last_saved = datetime.fromisoformat(_hist_with_ts[0]["saved_at"])
            _hours_since = (datetime.now() - _last_saved).total_seconds() / 3600
            # Typical cadence = median gap between the last few saved
            # entries' timestamps, when there are enough to compute one.
            _gaps = []
            for _a, _b in zip(_hist_with_ts, _hist_with_ts[1:]):
                try:
                    _ga = datetime.fromisoformat(_a["saved_at"])
                    _gb = datetime.fromisoformat(_b["saved_at"])
                    _gaps.append(abs((_ga - _gb).total_seconds()) / 3600)
                except Exception:
                    pass
            _typical_cadence = sorted(_gaps)[len(_gaps) // 2] if len(_gaps) >= 2 else 24
            _threshold = max(24, min(72, _typical_cadence * 1.5))
            if _hours_since > _threshold:
                _ago = f"{_hours_since/24:.1f} days" if _hours_since >= 48 else f"{_hours_since:.0f} hours"
                st.markdown(
                    f'<div class="notice">'
                    f'<strong>Last update for \u201c{_html.escape(st.session_state.team_name or "default")}\u201d was {_ago} ago</strong> '
                    f'\u2014 typical cadence is about {_typical_cadence:.0f}h.</div>',
                    unsafe_allow_html=True
                )
        except Exception:
            pass

# ═══════════════════════════════════════════════════
# CONFIGURATION (lives in Customize > Style)
# ═══════════════════════════════════════════════════
with _cz_tabs[0]:
    cfg1, cfg3 = st.columns(2)
    cfg2, cfg4 = st.columns(2)
    with cfg1:
        standup_date = st.date_input(T("standup_date"), value=date.today(), key="pref_date")
    with cfg2:
        tone_choice = st.radio(T("tone"), options=list(TONE_OPTIONS.keys()), index=1, key="pref_tone",
                               horizontal=True, format_func=_plain_label)
    with cfg3:
        domain_choice = st.selectbox(T("domain"), options=list(DOMAIN_OPTIONS.keys()), index=0, key="pref_domain",
                                         format_func=_plain_label)
        _prev_raw = st.session_state.get("raw_input", "")
        _suggested_domain = suggest_domain(_prev_raw)
        if _suggested_domain and _suggested_domain != domain_choice:
            if st.button(f"Use suggested: {_plain_label(_suggested_domain)}", key="apply_suggested_domain"):
                st.session_state.pref_domain = _suggested_domain
                st.rerun()
    with cfg4:
        lang_choice = st.radio(T("out_lang"), options=list(OUTPUT_LANG_OPTIONS.keys()), index=0, key="pref_lang",
                               horizontal=True, format_func=_plain_label)

    cfg5, cfg6, cfg7 = st.columns(3)
    with cfg5:
        # Pre-fill from the most recent saved entry — a lightweight "remembered"
        # default rather than a separate storage mechanism, since the same
        # persistent history file already carries this information.
        _remembered_project = ""
        if st.session_state.history and st.session_state.history[0].get("project") not in (None, "—"):
            _remembered_project = st.session_state.history[0]["project"]
        if "pref_project" not in st.session_state:
            st.session_state["pref_project"] = _remembered_project
        project_name = st.text_input(T("project_tag"),
                                     placeholder="e.g. Phoenix · Sprint 14", key="pref_project")
    with cfg6:
        include_tomorrow = st.toggle(T("incl_tomorrow"), value=False, key="pref_tomorrow")
    with cfg7:
        include_blockers = st.toggle(T("hl_blockers"), value=True, key="pref_blockers")

    if "pref_your_name" not in st.session_state:
        st.session_state.pref_your_name = load_shared_settings().get("your_name", "")
    your_name = st.text_input("Your name (optional \u2014 used as \u2018Prepared by\u2019 in exports \u00b7 shared with SatiCast)",
                              placeholder="e.g. Pranay", key="pref_your_name")
    if your_name.strip():
        save_shared_settings({"your_name": your_name.strip()})

    # 30 / 41 / 40: output template, interface language, high contrast (state seeded once at the top; key-only widgets)
    ui1, ui2, ui3 = st.columns(3)
    with ui1:
        st.selectbox(T("template"), options=list(TEMPLATES.keys()), key="pref_template", on_change=_save_ui_prefs,
                     help="Standup keeps the classic output. The others swap the narrative instructions and the tab labels.")
    with ui2:
        st.selectbox(T("ui_lang"), options=list(UI_LANG_OPTIONS.keys()), key="pref_ui_lang", on_change=_save_ui_prefs,
                     help="Language of the app's own labels. The language of the generated update is the 'Output language' setting above.")
    with ui3:
        st.toggle(T("high_contrast"), key="pref_contrast", on_change=_save_ui_prefs,
                  help="Stronger text and border contrast. Also follows your system's 'increase contrast' setting.")

# ── SETTINGS EXPORT / IMPORT — same idea as SatiCast's: download your
# preferences as JSON, restore them on a fresh browser/session. ──
with _cz_tabs[4]:
    st.markdown('<div class="eyebrow">Export / import settings</div>', unsafe_allow_html=True)
    _settings_snapshot = {
        "pref_tone": st.session_state.get("pref_tone"),
        "pref_domain": st.session_state.get("pref_domain"),
        "pref_lang": st.session_state.get("pref_lang"),
        "pref_project": st.session_state.get("pref_project"),
        "pref_tomorrow": st.session_state.get("pref_tomorrow"),
        "pref_blockers": st.session_state.get("pref_blockers"),
        "pref_your_name": st.session_state.get("pref_your_name"),
        "pref_template": st.session_state.get("pref_template"),
        "pref_ui_lang": st.session_state.get("pref_ui_lang"),
        "pref_contrast": st.session_state.get("pref_contrast"),
        "pref_brand_project": st.session_state.get("pref_brand_project"),
    }
    ecol1, ecol2 = st.columns(2)
    with ecol1:
        st.download_button(
            "Download my settings", data=json.dumps(_settings_snapshot, indent=2),
            file_name="sanghastatus_settings.json", mime="application/json",
            key="dl_settings_btn", use_container_width=True
        )
    with ecol2:
        _uploaded_settings = st.file_uploader("Restore from file", type=["json"], key="settings_upload", label_visibility="collapsed")
        if _uploaded_settings is not None:
            try:
                _restored = json.load(_uploaded_settings)
                for _k, _v in _restored.items():
                    if _v is not None:
                        st.session_state[_k] = _v
                _notify_next_run("Settings restored")
                st.rerun()
            except Exception as e:
                st.error(f"Couldn't read that settings file: {e}")

# ── 38 / 45: team backup & restore, what's stored, reset ──
st.session_state.setdefault("_backup_uploader_n", 0)
with _cz_tabs[4]:
    st.markdown('<div class="eyebrow" style="margin-top:1.5rem;">Team backup \u00b7 roster, presets, glossary, history, sprint goal, logo</div>', unsafe_allow_html=True)
    st.caption("Exports the CURRENT team only. The PIN hash is never included.")
    _dl_button("Download team backup (.json)", data=json.dumps(build_backup(), indent=2, default=str),
               file_name=f"sanghastatus_backup_{TEAM_SLUG}_{date.today().isoformat()}.json", mime="application/json", key="dl_backup")
    _bk_file = st.file_uploader("Restore a team backup", type=["json"], key=f"backup_upload_{st.session_state['_backup_uploader_n']}")
    if _bk_file is not None:
        try:
            _bk_obj = json.loads(_bk_file.getvalue().decode("utf-8"))
        except Exception:
            _bk_obj = None
        _bk_ok, _bk_msg = validate_backup(_bk_obj)
        if not _bk_ok:
            st.error(_bk_msg)
        else:
            st.markdown(
                '<div class="hint-card warn" role="alert"><div class="hint-title"><span class="glyph" aria-hidden="true">\u26a0</span> Confirm restore</div>'
                f'<div class="hint-body">This replaces the current team\u2019s roster ({len(_bk_obj.get("roster", {}))}), presets ({len(_bk_obj.get("presets", {}))}), '
                f'glossary ({len(_bk_obj.get("glossary", []))}), history ({len(_bk_obj.get("history", []))} entries), sprint goal and logo with the backup\u2019s '
                f'(taken from team \u201c{_html.escape(str(_bk_obj.get("team", "?")))}\u201d, {_html.escape(str(_bk_obj.get("exported_at", "?")))}).</div></div>',
                unsafe_allow_html=True)
            if st.button("Yes, restore this backup", key="sec_backup_confirm_btn"):
                apply_backup(_bk_obj)
                st.session_state.pop("last_output", None)
                st.session_state["_backup_uploader_n"] += 1
                st.session_state.pop(f"sprint_goal_input_{TEAM_SLUG}", None)
                _notify_next_run("Backup restored")
                st.rerun()

    st.markdown('<div class="eyebrow" style="margin-top:1.5rem;">What\u2019s stored for this team</div>', unsafe_allow_html=True)
    st.markdown(
        '<table class="bk-table"><caption class="sr-only">Stored data for this team</caption><thead><tr><th>Item</th><th>Count</th><th>Where</th></tr></thead><tbody>'
        + "".join(f"<tr><td>{_html.escape(str(a))}</td><td>{_html.escape(str(b))}</td><td>{_html.escape(str(c))}</td></tr>" for a, b, c in stored_data_summary())
        + "</tbody></table>", unsafe_allow_html=True)
    st.caption("Read-only. No secrets or PIN hash are shown. Preference keys in this session: " + (", ".join(sorted(k for k in st.session_state.keys() if isinstance(k, str) and k.startswith("pref_"))) or "none"))
    st.markdown('<div class="eyebrow" style="margin-top:1.25rem;">' + _html.escape(T("reset")) + '</div>', unsafe_allow_html=True)
    st.caption("Resets tone, domain, language, template, interface language, contrast and project tag for this team. History, roster, glossary and presets are kept.")
    _rst_ok = st.checkbox("I understand \u2014 reset this team\u2019s preferences to defaults", key="reset_confirm_chk")
    if st.button("Reset preferences", key="sec_reset_prefs_btn", disabled=not _rst_ok):
        reset_team_preferences()
        st.session_state.pop("reset_confirm_chk", None)
        _notify_next_run("Preferences reset to defaults")
        st.rerun()

# ── 29 / 32: sprint goal editor + brand (logo / project header) ──
with _cz_tabs[5]:
    st.markdown('<div class="eyebrow">' + _html.escape(T("sprint_goal")) + ' \u00b7 tasks are linked to it by keyword overlap</div>', unsafe_allow_html=True)
    _goal_key = f"sprint_goal_input_{TEAM_SLUG}"
    if _goal_key not in st.session_state:
        st.session_state[_goal_key] = load_sprint_goal()
    st.text_input("Sprint goal", key=_goal_key, placeholder="e.g. Ship the payment gateway integration and stabilise the backend")
    _g1, _g2, _ = st.columns([1, 1, 3])
    with _g1:
        if st.button("Save goal", key="sec_save_goal_btn"):
            save_sprint_goal(st.session_state[_goal_key].strip())
            _notify_next_run("Sprint goal saved")
            st.rerun()
    with _g2:
        if st.button("Clear", key="sec_clear_goal_btn"):
            save_sprint_goal("")
            st.session_state.pop(_goal_key, None)
            st.rerun()

with _cz_tabs[6]:
    st.markdown('<div class="eyebrow">Branded PDF \u00b7 project name & logo</div>', unsafe_allow_html=True)
    st.text_input("Project name for the PDF header", key="pref_brand_project", on_change=_save_ui_prefs,
                  placeholder="Defaults to the project / sprint tag")
    _logo_now = load_logo()
    _up = st.file_uploader("Logo (PNG or JPG, up to 1 MB)", type=["png", "jpg", "jpeg"], key="logo_upload")
    if _up is not None:
        _ub = _up.getvalue()
        _uh = hashlib.md5(_ub).hexdigest()
        if st.session_state.get("_logo_saved_hash") != _uh:
            _mime, _lerr = validate_logo(_up.name, _ub)
            if _lerr:
                st.error(_lerr)
            else:
                save_logo(_mime, _ub)
                st.session_state["_logo_saved_hash"] = _uh
                _logo_now = load_logo()
                _notify("Logo saved for this team")
    if _logo_now:
        st.image(_logo_now[1], width=120, caption="Current logo (used in the PDF header)")
        if st.button("Remove logo", key="sec_remove_logo_btn"):
            delete_logo()
            st.session_state.pop("_logo_saved_hash", None)
            _notify_next_run("Logo removed")
            st.rerun()

# ── CROSS-TEAM ROLLUP — since multi-team support already stores each
# team's SQLite DB as its own file (".sanghastatus[_<slug>].db"), this
# scans the deployment's local disk for every such file, loads each
# team's MOST RECENT saved standup, and shows a quick health/top-blocker
# comparison across teams — without switching "current team" above. Only
# shown at all when more than one team's data actually exists on disk. ──
def _discover_team_db_files() -> list:
    import glob as _glob
    found = []
    for p in sorted(_glob.glob(".sanghastatus*.db")):
        m = re.match(r'^\.sanghastatus(?:_(.+))?\.db$', p)
        if m:
            found.append((m.group(1) or "default", p))
    return found


def _load_team_rollup_snapshot(db_path: str):
    """Best-effort: latest saved entry's health score + top blocker for
    one team's DB file. Never raises — returns None on any problem (e.g.
    a locked/corrupt/mid-write DB file) so one bad team can't break the
    whole rollup view."""
    try:
        conn = sqlite3.connect(db_path)
        row = conn.execute(
            "SELECT date, members_detail_json FROM history ORDER BY id DESC LIMIT 1"
        ).fetchone()
        conn.close()
        if not row:
            return None
        members_detail = json.loads(row[1] or "[]")
        score, label = compute_health_score(members_detail, {}, {})
        all_blockers = [b for m in members_detail for b in m.get("blockers", [])]
        return {
            "date": row[0], "score": score, "label": label,
            "top_blocker": all_blockers[0] if all_blockers else "—",
            "blocker_count": len(all_blockers),
        }
    except Exception:
        return None


_team_db_files = _discover_team_db_files()
if len(_team_db_files) > 1:
    with _cz_tabs[1]:
        st.markdown(f'<div class="eyebrow" style="margin-top:1.5rem;">All teams ({len(_team_db_files)}) \u00b7 cross-team snapshot</div>', unsafe_allow_html=True)
        st.caption("Each row is that team's MOST RECENT saved standup — not a live view into another team's roster or full history.")
        _rollup_rows = []
        for _slug, _dbp in _team_db_files:
            _snap = _load_team_rollup_snapshot(_dbp)
            _rollup_rows.append({
                "Team": _slug + (" (current)" if _slug == TEAM_SLUG else ""),
                "Latest standup": _snap["date"] if _snap else "—",
                "Health": f"{_snap['score']} ({_snap['label']})" if _snap else "No data",
                "Top blocker": (_snap["top_blocker"][:80] if _snap else "—"),
                "Blockers": _snap["blocker_count"] if _snap else 0,
            })
        import pandas as _pd
        st.dataframe(_pd.DataFrame(_rollup_rows), use_container_width=True, hide_index=True)

# ── TEMPLATE / PRESET LIBRARY — save the current tone/domain/output-
# language/format choices as a named preset (local JSON, same persistence
# pattern as roster/history) and reload one by name later. ──
with _cz_tabs[2]:
    st.markdown('<div class="eyebrow">Presets \u00b7 save & reload tone/domain/language combos</div>', unsafe_allow_html=True)
    _presets = load_presets()
    pcol1, pcol2 = st.columns([2, 1])
    with pcol1:
        _new_preset_name = st.text_input("Preset name", placeholder="e.g. HR Weekly, Eng Standup Formal…", key="new_preset_name")
    with pcol2:
        st.write("")
        if st.button("Save preset", key="sec_save_preset_btn", use_container_width=True):
            if _new_preset_name.strip():
                _presets[_new_preset_name.strip()] = {
                    "tone": st.session_state.get("pref_tone"),
                    "domain": st.session_state.get("pref_domain"),
                    "lang": st.session_state.get("pref_lang"),
                    "tomorrow": st.session_state.get("pref_tomorrow"),
                    "blockers": st.session_state.get("pref_blockers"),
                }
                save_presets(_presets)
                _notify_next_run(f"Saved preset \u2018{_new_preset_name.strip()}\u2019")
                st.rerun()
            else:
                st.warning("Give the preset a name first.")

    if _presets:
        lcol1, lcol2 = st.columns([2, 1])
        with lcol1:
            _picked_preset = st.selectbox("Load a preset", options=list(_presets.keys()), key="load_preset_pick")
        with lcol2:
            st.write("")
            if st.button("Apply", key="sec_apply_preset_btn", use_container_width=True):
                _p = _presets[_picked_preset]
                if _p.get("tone") in TONE_OPTIONS:
                    st.session_state.pref_tone = _p["tone"]
                if _p.get("domain") in DOMAIN_OPTIONS:
                    st.session_state.pref_domain = _p["domain"]
                if _p.get("lang") in OUTPUT_LANG_OPTIONS:
                    st.session_state.pref_lang = _p["lang"]
                if "tomorrow" in _p:
                    st.session_state.pref_tomorrow = _p["tomorrow"]
                if "blockers" in _p:
                    st.session_state.pref_blockers = _p["blockers"]
                _notify_next_run(f"Applied preset \u2018{_picked_preset}\u2019")
                st.rerun()
        if st.button("Delete this preset", key="sec_delete_preset_btn"):
            _presets.pop(_picked_preset, None)
            save_presets(_presets)
            st.rerun()
    else:
        st.caption("No presets saved yet — configure the options above, then save one.")

# ── TEAM GLOSSARY — jargon/acronym expansions injected verbatim into the
# generation prompt so the LLM uses the team's own terms instead of
# paraphrasing them. Persisted the same way as roster/presets. ──
with _cz_tabs[3]:
    st.markdown('<div class="eyebrow">Team glossary \u00b7 jargon & acronyms the AI should use verbatim</div>', unsafe_allow_html=True)
    _glossary = load_glossary()
    gcol1, gcol2, gcol3 = st.columns([1.2, 2, 0.8])
    with gcol1:
        _new_term = st.text_input("Term / acronym", placeholder="e.g. UAT", key="new_glossary_term")
    with gcol2:
        _new_expansion = st.text_input("Expansion", placeholder="e.g. User Acceptance Testing", key="new_glossary_expansion")
    with gcol3:
        st.write("")
        if st.button("Add", key="sec_add_glossary_btn", use_container_width=True):
            if _new_term.strip() and _new_expansion.strip():
                _glossary = [g for g in _glossary if g.get("term", "").lower() != _new_term.strip().lower()]
                _glossary.append({"term": _new_term.strip(), "expansion": _new_expansion.strip()})
                save_glossary(_glossary)
                st.rerun()
            else:
                st.warning("Fill in both the term and its expansion first.")

    if _glossary:
        for _gi, _g in enumerate(_glossary):
            gr1, gr2, gr3 = st.columns([1.2, 2, 0.8])
            with gr1:
                st.caption(f"**{_g['term']}**")
            with gr2:
                st.caption(_g['expansion'])
            with gr3:
                if st.button("🗑️", key=f"sec_del_glossary_{_gi}", help="Remove this entry"):
                    _glossary.pop(_gi)
                    save_glossary(_glossary)
                    st.rerun()
    else:
        st.caption("No glossary entries yet — add a term above so the AI uses your team's own vocabulary.")


# ═══════════════════════════════════════════════════
# RAW UPDATES CARD
# ═══════════════════════════════════════════════════
st.markdown(
    '<div class="section-head">'
    f'<div class="eyebrow">{_html.escape(T("step1"))}</div>'
    f'<h2>{_html.escape(T("step1_title"))}</h2>'
    f'<p>{_html.escape(T("step1_sub"))}</p>'
    '</div>',
    unsafe_allow_html=True
)

raw_updates = st.text_area(
    "Paste team updates below:",
    placeholder="""Alice:
- Working on API integration with payment gateway.
- Resolving backend timeout issues.
- Tomorrow: complete unit tests.

Bob:
- Preparing regression test cases for release.
- Blocked on UAT environment access from DevOps.

Carol:
- Deployed hotfix to staging.
- Reviewing PR for auth module.
""",
    label_visibility="collapsed",
    key="raw_input",
    help="🎙️ Tip: use your keyboard's dictation button (mic icon on the on-screen/OS keyboard) to speak your update — it types straight into this box like any other text."
)

if GITHUB_PULL_ENABLED:
    if st.button(f"Pull my GitHub activity (last 24h) \u2014 {GITHUB_USERNAME}", key="pull_github_btn"):
        gh_bullets = fetch_github_activity(24)
        if gh_bullets:
            existing = st.session_state.get("raw_input", "")
            block = f"{GITHUB_USERNAME}:\n" + "\n".join(gh_bullets)
            st.session_state.raw_input = (existing.rstrip() + "\n\n" + block).strip() if existing.strip() else block
            st.rerun()
        else:
            st.caption("No GitHub activity found in the last 24h, or the pull failed.")

def _do_prefill():
    _txt = build_prefill_text(st.session_state.history)
    if not _txt:
        st.session_state["_prefill_msg"] = "No saved standup yet to carry over from."
        return
    _cur = st.session_state.get("raw_input", "").strip()
    st.session_state["raw_input"] = (_cur + "\n\n" + _txt) if _cur else _txt
    st.session_state["_prefill_msg"] = "Filled with yesterday\u2019s open tasks and unresolved blockers \u2014 edit as needed."


st.button(T("prefill"), key="prefill_btn", on_click=_do_prefill,
          help="Adds each member's still-open tasks and unresolved blockers from the last saved standup")
_pf_msg = st.session_state.pop("_prefill_msg", "")
if _pf_msg:
    st.caption(_pf_msg)

# ── QUICK POLL / Q&A — Streamlit has no live multi-user voting, so this is
# a lightweight "attach a question" feature: whatever's typed here gets
# appended as a footer to the chat/WhatsApp outputs so the team sees it
# and can reply in the same thread, rather than a real-time poll widget. ──
qq_col1, qq_col2 = st.columns([5, 1])
with qq_col1:
    quick_question = st.text_input(
        "Quick team question (optional) \u2014 appended to Chat & WhatsApp updates",
        placeholder="e.g. Thumbs up if Friday's demo time still works for everyone?",
        key="quick_poll_question"
    )
with qq_col2:
    st.write("")
    st.write("")
    if st.button("Suggest", key="sec_icebreaker_btn", help="Fill the question above with a random icebreaker you can edit or accept", use_container_width=True):
        import random as _random
        st.session_state.quick_poll_question = _random.choice(ICEBREAKER_QUESTIONS)
        st.rerun()

_day_segments = split_multi_day_paste(raw_updates) if raw_updates.strip() else []
if _day_segments:
    st.caption(f"Looks like {len(_day_segments)} days' worth of updates pasted at once — pick one to generate now (paste the rest again later, or use \u201cLoad this day\u201d to swap in a different day).")
    day_labels = [lbl for lbl, _ in _day_segments]
    dcol1, dcol2 = st.columns([3, 1])
    with dcol1:
        picked_day_label = st.selectbox("Which day to generate for right now?", options=day_labels, key="multi_day_pick")
    with dcol2:
        st.write("")
        if st.button("Load this day", key="load_multi_day", use_container_width=True):
            picked_raw = next(txt for lbl, txt in _day_segments if lbl == picked_day_label)
            st.session_state.raw_input = picked_raw
            st.rerun()

# If the paste looks like an exported chat thread ('[Name] HH:MM' /
# 'Name HH:MM' repeated headers) rather than the plain 'Name:' + bullets
# format, preprocess it into that shape first — a no-op otherwise.
_effective_raw = preprocess_chat_thread_paste(raw_updates) if raw_updates.strip() else raw_updates
_was_thread_paste = _effective_raw != raw_updates
members = parse_members(_effective_raw) if raw_updates.strip() else []
if _was_thread_paste and members:
    st.caption("Detected a chat-thread export paste — auto-split into per-person updates.")

_warn = looks_malformed(raw_updates, members)
if _warn and raw_updates.strip():
    st.caption(f"Heads up: {_warn}")

# ── 37: inline input-validation hints (deterministic, before Generate) ──
_hints = validate_input(raw_updates, members, expect_blockers=bool(st.session_state.get("pref_blockers", True)))
if _hints:
    st.markdown(
        '<div class="hint-card" role="note"><div class="hint-title"><span class="glyph" aria-hidden="true">\u24d8</span> '
        f'Before you generate \u2014 {len(_hints)} thing{"s" if len(_hints) != 1 else ""} to check</div><ul>'
        + "".join(f"<li>{_html.escape(h)}</li>" for h in _hints) + "</ul></div>",
        unsafe_allow_html=True
    )

# ── 35: sensitive-data scrubber — warn + "Mask before sending" (default ON). Masks the PROMPT payload only. ──
st.session_state.setdefault("scrub_mask", True)
_scrub_found = mask_sensitive(_effective_raw)[1] if raw_updates.strip() else []
if _scrub_found:
    _items = ", ".join(f"{f['count']}\u00d7 {f['type'].replace('-', ' ').lower()} ({_html.escape(f['preview'])})" for f in _scrub_found)
    st.markdown(
        '<div class="hint-card warn" role="alert"><div class="hint-title"><span class="glyph" aria-hidden="true">\u26a0</span> '
        f'Sensitive data detected in your notes</div><div class="hint-body">Found: {_items}. '
        'Secrets and personal details should not be sent to an AI model.</div></div>',
        unsafe_allow_html=True
    )
    st.toggle("Mask before sending (replaces them with [REDACTED-TYPE] in what the AI sees; your notes stay as typed)", key="scrub_mask")

if members:
    total_tasks    = sum(m["count"] for m in members)
    total_blockers = sum(len(m["blockers"]) for m in members)
    st.markdown(
        f'<div class="section-head" style="margin-bottom:0;"><div class="eyebrow">{_html.escape(T("step2"))}</div><h2>{_html.escape(T("step2_title"))}</h2></div>',
        unsafe_allow_html=True
    )
    st.markdown(
        f'<div class="stats-row reveal">'
        f'<div class="stat-chip"><div class="stat-val">{len(members)}</div><div class="stat-lbl">{T("members")}</div></div>'
        f'<div class="stat-chip"><div class="stat-val">{total_tasks}</div><div class="stat-lbl">{T("tasks")}</div></div>'
        f'<div class="stat-chip"><div class="stat-val">{total_blockers}</div><div class="stat-lbl">{T("blockers")}</div></div>'
        f'</div>',
        unsafe_allow_html=True
    )

    # ── SPRINT/VELOCITY TRENDLINE — smooth thin SVG line chart of total
    # tasks vs. blockers across the last (up to) 8 saved entries. ──
    if st.session_state.history:
        _velo_entries = list(reversed(st.session_state.history[:8]))  # oldest->newest
        _tv = [e.get("tasks", 0) for e in _velo_entries]
        _bv = [sum(len(m.get("blockers", [])) for m in e.get("members_detail", [])) for e in _velo_entries]
        _n = len(_velo_entries)
        _W, _H, _PAD = 600, 150, 14
        _ymax = max(_tv + _bv + [1])

        def _pt(i, v):
            x = _PAD + ((_W - 2 * _PAD) * i / (_n - 1) if _n > 1 else (_W - 2 * _PAD) / 2)
            y = _H - _PAD - (v / _ymax) * (_H - 2 * _PAD)
            return x, y

        def _smooth_path(vals):
            pts = [_pt(i, v) for i, v in enumerate(vals)]
            if len(pts) == 1:
                return f"M{pts[0][0]:.1f},{pts[0][1]:.1f}"
            d = f"M{pts[0][0]:.1f},{pts[0][1]:.1f}"
            for i in range(len(pts) - 1):
                p0 = pts[i - 1] if i > 0 else pts[i]
                p1, p2 = pts[i], pts[i + 1]
                p3 = pts[i + 2] if i + 2 < len(pts) else pts[i + 1]
                c1 = (p1[0] + (p2[0] - p0[0]) / 6, p1[1] + (p2[1] - p0[1]) / 6)
                c2 = (p2[0] - (p3[0] - p1[0]) / 6, p2[1] - (p3[1] - p1[1]) / 6)
                d += f" C{c1[0]:.1f},{c1[1]:.1f} {c2[0]:.1f},{c2[1]:.1f} {p2[0]:.1f},{p2[1]:.1f}"
            return d

        _grid = "".join(
            f'<line class="trend-grid" x1="0" x2="{_W}" y1="{y}" y2="{y}"/>' for y in (_PAD, _H / 2, _H - _PAD)
        )
        _dots = ""
        for _series, _vals, _col in (("tasks", _tv, "var(--cta)"), ("blockers", _bv, "var(--sev2)")):
            for i, v in enumerate(_vals):
                x, y = _pt(i, v)
                _dots += (f'<circle cx="{x:.1f}" cy="{y:.1f}" r="4" fill="var(--card)" stroke="{_col}" stroke-width="2">'
                          f'<title>{v} {_series} on {_html.escape(_velo_entries[i].get("date", "?"))}</title></circle>')
        _xlabels = "".join(
            f'<span style="left:{_pt(i, 0)[0] / _W * 100:.1f}%;">{_html.escape(e.get("date", "?").split(",")[0])}</span>'
            for i, e in enumerate(_velo_entries)
        )
        st.markdown(
            f'<div class="trend-card reveal">'
            f'<div class="trend-head"><div><div class="eyebrow">Sprint trend</div>'
            f'<div style="font-size:1.1875rem;font-weight:600;letter-spacing:-0.015em;">Tasks vs. blockers \u00b7 last {_n}</div></div>'
            f'<div class="trend-legend"><span><i style="background:var(--cta)"></i>Tasks</span>'
            f'<span><i style="background:var(--sev2)"></i>Blockers</span></div></div>'
            f'<div class="trend-plot"><svg viewBox="0 0 {_W} {_H}" role="img" aria-label="Tasks and blockers across the last {_n} standups">'
            f'{_grid}'
            f'<path class="trend-line" pathLength="1" d="{_smooth_path(_tv)}" stroke="var(--cta)"/>'
            f'<path class="trend-line" pathLength="1" d="{_smooth_path(_bv)}" stroke="var(--sev2)" style="animation-delay:0.15s"/>'
            f'{_dots}</svg>'
            f'<div class="trend-x">{_xlabels}</div></div>'
            f'</div>',
            unsafe_allow_html=True
        )

    _roster = load_roster()

    # ── CAPACITY / PTO — "Who's out today?" excludes those members from the
    # narrative prompt context and from blocker-escalation nagging for the
    # day, without deleting their pasted update from the raw text. ──
    _out_today = st.multiselect(
        T("whos_out") + " (excluded from escalation nagging; noted in the generated narrative)",
        options=[m["name"] for m in members], default=[], key="out_today_members"
    )

    # ── VIEW TOGGLE — compact table vs. the default card view, useful once
    # a team has more than a handful of members. ──
    _view_mode = st.radio(
        "View", options=["🔲 Cards", "📊 Table"], horizontal=True,
        key="member_view_mode", label_visibility="collapsed", format_func=_plain_label
    )

    chips = ""
    # Stable per-NAME hue (not list position) so a person's avatar keeps the
    # same, gently desaturated colour across runs/days.
    avatar_colors = [8, 24, 42, 96, 150, 172, 196, 214, 236, 268, 300, 336]
    _member_names = [m["name"] for m in members]
    _table_rows = []
    for i, m in enumerate(members):
        # @mention tags inside blocker text become small pills (pure string matching).
        _tagged_blockers = [tag_mentions(b, _member_names) for b in m["blockers"]]
        _n_b = len(m["blockers"])
        bl = (f'<div class="chip-block">{"; ".join(_tagged_blockers)}</div>' if _tagged_blockers else "")
        initial = _html.escape(m["name"].strip()[:1].upper() or "?")
        _name_hash = int(hashlib.md5(m["name"].strip().lower().encode()).hexdigest(), 16)
        hue = avatar_colors[_name_hash % len(avatar_colors)]
        role = _roster.get(m["name"].lower(), {}).get("role", "")
        role_html = f'<span class="chip-role">{_html.escape(role)}</span>' if role else ""
        _is_out = m["name"] in _out_today
        _badges = f'<span class="pill">{m["count"]} task{"s" if m["count"] != 1 else ""}</span>'
        if _n_b:
            _badges += f'<span class="pill pill-block"><span aria-hidden="true">\u26a0</span> {_n_b} blocker{"s" if _n_b > 1 else ""}</span>'
        if _is_out:
            _badges += '<span class="pill pill-out">Out today</span>'
        chips += (
            f'<div class="member-chip" style="--h:{hue};{"opacity:0.55;" if _is_out else ""}">'
            f'<div class="mc-avatar">{initial}</div>'
            f'<div class="mc-main"><div class="mc-top"><span class="chip-name">{_html.escape(m["name"])}</span>{role_html}</div>'
            f'<div class="mc-badges">{_badges}</div>{bl}</div></div>'
        )
        _table_rows.append({
            "Name": m["name"] + (" 🏖️" if _is_out else ""), "Role": role or "—",
            "Tasks": m["count"], "Blockers": len(m["blockers"]),
        })

    if _view_mode == "📊 Table":
        import pandas as _pd
        st.dataframe(_pd.DataFrame(_table_rows), use_container_width=True, hide_index=True)
    else:
        st.markdown(f'<div class="member-chips reveal">{chips}</div>', unsafe_allow_html=True)

    # ── STANDUP HEALTH SCORE — a simple 0-100 composite heuristic badge
    # (see compute_health_score()'s docstring for the exact formula) —
    # this is a rough signal, not a scientific metric or a judgment about
    # any individual. Members marked out-today are excluded so a day off
    # doesn't get counted as a brief/silent update or a dropped blocker. ──
    _active_members = [m for m in members if m["name"] not in _out_today]
    # 43: heavy-ish pure analytics cached on their inputs (not recomputed on every widget rerun)
    _an = _c_analytics(json.dumps(members), json.dumps(st.session_state.history, default=str), json.dumps(list(_out_today)))
    _brief_flags_now, _escalations_now = _an["brief"], _an["esc"]
    _health_score, _health_label = _an["score"], _an["label"]
    _health_color = ("#34c759" if _health_score >= 85 else "#ffb020" if _health_score >= 60
                      else "#ff8a3d" if _health_score >= 35 else "#ff453a")
    _hr_c = 2 * 3.14159265 * 34
    _hr_off = _hr_c * (1 - max(0, min(100, _health_score)) / 100)
    st.markdown(
        f'<div class="health-badge badge-pill reveal" title="Heuristic only \u2014 combines blocker count, recurring-blocker count, and brevity flags. Not a scientific metric.">'
        f'<div class="health-ring"><svg viewBox="0 0 84 84" aria-hidden="true">'
        f'<circle class="hr-track" cx="42" cy="42" r="34" fill="none" stroke-width="7"/>'
        f'<circle class="hr-val" cx="42" cy="42" r="34" fill="none" stroke-width="7" stroke-linecap="round" '
        f'stroke="{_health_color}" stroke-dasharray="{_hr_c:.2f}" stroke-dashoffset="{_hr_off:.2f}" style="--hr-c:{_hr_c:.2f}"/></svg>'
        f'<div class="hr-num">{_health_score}</div></div>'
        f'<div><div class="eyebrow">Standup health</div><div class="health-label"><span aria-hidden="true">{_HEALTH_GLYPH.get(str(_health_label), "")}</span> {_html.escape(str(_health_label))}</div>'
        f'<div class="health-sub">Heuristic from blocker &amp; brevity signals \u2014 not a scientific metric</div></div>'
        f'</div>',
        unsafe_allow_html=True
    )

    # ── TEAM PULSE — optional, self-reported, SESSION-ONLY (never written to
    # disk, never shown per-person). Each tap is an anonymous data point that
    # only ever surfaces as a team-level aggregate, in the same spirit as
    # flag_brief_updates()'s "purely objective... NOT sentiment/emotion
    # analysis" stance — this is a self-report, not an inference. ──
    with st.expander("Team pulse \u2014 optional, anonymous team-level mood check", expanded=False):
        st.caption("Tap how the team's feeling overall today. This is never stored per-person or saved to disk — it's just a same-run, anonymous snapshot.")
        MOOD_OPTIONS = {"Skip": None, "😞 Rough": 1, "😐 Okay": 2, "🙂 Good": 3, "😄 Great": 4}
        pulse_cols = st.columns(len(members)) if len(members) <= 6 else [st.container()] * len(members)
        pulse_taps = []
        for i, m in enumerate(members):
            with pulse_cols[i]:
                pick = st.select_slider(
                    m["name"], options=list(MOOD_OPTIONS.keys()), value="Skip",
                    key=f"pulse_{m['name'].lower()}", label_visibility="visible"
                )
                if MOOD_OPTIONS[pick] is not None:
                    pulse_taps.append(MOOD_OPTIONS[pick])
        if pulse_taps:
            avg = sum(pulse_taps) / len(pulse_taps)
            pulse_emoji = "😄" if avg >= 3.5 else "🙂" if avg >= 2.5 else "😐" if avg >= 1.5 else "😞"
            pulse_word = "Great" if avg >= 3.5 else "Good" if avg >= 2.5 else "Okay" if avg >= 1.5 else "Rough"
            tally = ", ".join(f"{pulse_taps.count(v)}× {k.split(' ')[0]}" for k, v in MOOD_OPTIONS.items() if v and v in pulse_taps)
            st.markdown(
                f'<div class="badge-pill badge-info" style="font-size:0.9rem;">'
                f'{pulse_emoji} <strong>Team pulse today: {pulse_word}</strong> — based on {len(pulse_taps)} of {len(members)} response(s) ({tally})'
                f'<div style="opacity:0.65;font-size:0.75rem;margin-top:0.2rem;">Aggregate only — no individual response is shown or saved.</div>'
                f'</div>',
                unsafe_allow_html=True
            )
        else:
            st.caption("No responses yet — this stays blank unless someone taps a mood above.")

    # ── BURNOUT / OVERLOAD EARLY-WARNING — private to whoever has the app
    # open right now (the standup preparer). Deliberately NOT a permanent
    # badge on the member chip and NEVER included in any exported/shared
    # output (chat/email/Slack/Jira/etc.) — see flag_overload_trend()'s
    # docstring for why this stays a non-diagnostic cue, not a label. ──
    _overload_trend = _an["over"]
    if _overload_trend:
        with _sub_expander("Worth a check-in (private \u2014 not shown in any export)", expanded=False):
            st.caption(
                "Visible only here, to you, right now. Based purely on the same objective "
                "signals used elsewhere on this page (blocker persistence, update brevity, task "
                "count vs. their own baseline) — never a diagnosis, never shared or exported."
            )
            for _name, _reasons in _overload_trend.items():
                st.markdown(f"**{_name}** — " + "; ".join(_reasons))

    # ── TEAM ROSTER — profile memory (role tag per member, remembered
    # across runs so it doesn't need re-entering every standup) ──
    with st.expander("Team roster \u2014 tag each member\u2019s role (remembered next time)", expanded=False):
        roster_changed = False
        for m in members:
            key = m["name"].lower()
            current_role = _roster.get(key, {}).get("role", "")
            new_role = st.text_input(
                f"Role for {m['name']}", value=current_role,
                placeholder="e.g. Backend Engineer, QA Lead…",
                key=f"roster_role_{key}"
            )
            if new_role.strip() != current_role:
                _roster[key] = {"display": m["name"], "role": new_role.strip()}
                roster_changed = True
        if roster_changed:
            save_roster(_roster)

        # ── PER-PERSON HISTORICAL VIEW — pick a member, see their last up
        # to 5 saved entries' tasks side by side, pulled from
        # st.session_state.history filtered by name. ──
        st.markdown("---")
        st.caption("Per-person history — see a member's tasks across their last saved entries.")
        _roster_names = sorted({m["name"] for m in members} | {
            hm["name"] for e in st.session_state.history for hm in e.get("members_detail", [])
        })
        if _roster_names:
            _picked_hist_member = st.selectbox("Member", options=_roster_names, key="roster_hist_pick")
            _matches = []
            for e in st.session_state.history:
                hm = next((x for x in e.get("members_detail", []) if x["name"] == _picked_hist_member), None)
                if hm:
                    _matches.append((e.get("date", "?"), hm["tasks"]))
                if len(_matches) >= 5:
                    break
            if _matches:
                _hcols = st.columns(len(_matches))
                for _hc, (_hdate, _htasks) in zip(_hcols, _matches):
                    with _hc:
                        st.markdown(f"**{_hdate}**")
                        for _t in _htasks:
                            st.caption(f"• {_t}")
            else:
                st.caption(f"No saved entries yet mention {_picked_hist_member}.")

    # ── 27: blocker owner + needs-by (text inputs; goes into the prompt, the Blockers tab, the history entry) ──
    _all_blockers = [(m["name"], b) for m in members for b in m["blockers"]]
    if _all_blockers:
        with _sub_expander(f"Blocker owners & needed-by dates ({len(_all_blockers)})", expanded=False):
            st.caption("Optional. Added to the generated blockers and saved with this standup. \u201cNeeds by\u201d accepts a date or words like Friday / tomorrow / next week.")
            for _bn, _bt in _all_blockers:
                _bk = _bk_key(_bn, _bt)
                st.markdown(f"**{_html.escape(_bn)}** \u2014 {_html.escape(_bt)}")
                _b1, _b2 = st.columns(2)
                with _b1:
                    st.text_input(f"Owner \u00b7 {_bn}", key=f"bk_owner_{_bk}", placeholder="Who is unblocking this?")
                with _b2:
                    st.text_input(f"Needs by \u00b7 {_bn}", key=f"bk_due_{_bk}", placeholder="e.g. Friday or 2026-11-06")
                _due_txt = st.session_state.get(f"bk_due_{_bk}", "")
                if _due_txt.strip():
                    _rd = _resolve_due(_due_txt, standup_date)
                    st.caption(f"\u2192 {fmt_short_date(date.fromisoformat(_rd))}" if _rd else "Couldn\u2019t read that date \u2014 it will be kept as written.")

    # ── 29: sprint goal tracker ──
    _sprint_goal = load_sprint_goal()
    if _sprint_goal:
        _gm = map_tasks_to_goal(_sprint_goal, members)
        st.markdown(
            f'<div class="goal-card reveal"><div class="eyebrow">{_html.escape(T("sprint_goal"))}</div>'
            f'<div class="goal-text">{_html.escape(_sprint_goal)}</div>'
            f'<div class="goal-bar" role="progressbar" aria-valuemin="0" aria-valuemax="100" aria-valuenow="{_gm["pct"]}" aria-label="Tasks linked to the sprint goal">'
            f'<i style="width:{_gm["pct"]}%"></i></div>'
            f'<div class="goal-meta"><b>{_gm["pct"]}%</b> of tasks linked to the goal ({len(_gm["linked"])} of {len(_gm["linked"]) + len(_gm["unlinked"])})</div></div>',
            unsafe_allow_html=True)
        if _gm["unlinked"]:
            with _sub_expander(f"Not linked to the goal ({len(_gm['unlinked'])})", expanded=False):
                for _un, _ut in _gm["unlinked"]:
                    st.markdown(f"- \u25cb **{_html.escape(_un)}** \u2014 {_html.escape(_ut)}")

    # ── DIFF AGAINST YESTERDAY — actual side-by-side before/after ──
    if st.session_state.history:
        diffs = _an["diffs"]
        if diffs:
            rows = ""
            for name, pairs in diffs.items():
                for today_task, yesterday_task in pairs:
                    old_html, new_html = word_diff_html(yesterday_task, today_task)
                    rows += (
                        f'<div class="diff-row">'
                        f'<div class="diff-name">{name}</div>'
                        f'<div class="diff-cols">'
                        f'<div class="diff-col diff-yesterday"><span class="diff-label">Yesterday</span>{old_html}</div>'
                        f'<div class="diff-arrow"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M5 12h14M13 6l6 6-6 6"/></svg></div>'
                        f'<div class="diff-col diff-today"><span class="diff-label">Today</span>{new_html}</div>'
                        f'</div></div>'
                    )
            st.markdown(
                f'<div class="diff-panel reveal">'
                f'<div class="diff-panel-title">Possibly carried over from last update</div>'
                f'{rows}</div>',
                unsafe_allow_html=True
            )

        # ── BRIEF-UPDATE NOTICE — purely a word-count comparison against the
        # person's own history, NOT a claim about mood or wellbeing. Skips
        # anyone marked out-today, same as the health-score computation. ──
        brief_flags = _brief_flags_now
        if brief_flags:
            brief_lines = "".join(
                f'<div class="bp-line"><strong>{name}:</strong> '
                f'~{today}w vs usual ~{usual}w</div>'
                for name, (today, usual) in brief_flags.items()
            )
            st.markdown(
                f'<div class="badge-pill badge-info reveal">'
                f'<strong>Notably briefer than usual</strong> <span style="color:var(--txt-2)">(word count only)</span>{brief_lines}</div>',
                unsafe_allow_html=True
            )

        # ── BLOCKER ESCALATION — a blocker that has now shown up for the
        # same person across 2+ consecutive saved entries gets called out,
        # colored amber at 2 days and shifting to red at 3+ days, since a
        # blocker sitting untouched that long usually means it needs help
        # above the team. Anyone marked out-today is skipped — a blocker
        # they own doesn't age while they're away. ──
        escalations = _escalations_now
        if escalations:
            # Color shifts amber (2 days seen) → red (3+ days) instead of a
            # single flat red callout, so the longest-unresolved blockers
            # stand out visually from ones that just crossed the threshold.
            def _esc_color(days: int) -> str:
                if days >= 4:
                    return "var(--sev4)"  # deep red
                elif days == 3:
                    return "var(--sev3)"  # red/orange
                else:
                    return "var(--sev2)"  # amber (2 days — just below the 3-day threshold callout)

            esc_lines = "".join(
                f'<div class="bp-line" style="color:{_esc_color(days)} !important;">'
                f'<strong>{name}:</strong> "{text}" — seen {days} days running '
                f'<span class="sev-tag">{_sev_tag(days)}</span></div>'
                for name, items in escalations.items()
                for text, days in items
            )
            st.markdown(
                f'<div class="badge-pill badge-alert reveal">'
                f'<strong>Persisting blockers</strong> <span style="color:var(--txt-2)">(amber = 2 days, red = 3+ days)</span>{esc_lines}</div>',
                unsafe_allow_html=True
            )
else:
    # Small decorative inline SVG motif — soft blobs + a simple people/chat
    # icon in the app's own accent colors, same lightweight technique as
    # SatiCast's pill-decor SVGs (soft opacity, theme-colored shapes).
    _empty_svg = """
    <svg class="empty-state-decor" viewBox="0 0 180 70" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
      <circle cx="34" cy="35" r="26" style="fill:var(--accent);opacity:0.12"/>
      <circle cx="146" cy="24" r="17" style="fill:var(--txt-3);opacity:0.14"/>
      <circle cx="150" cy="52" r="11" style="fill:var(--accent);opacity:0.10"/>
      <g transform="translate(60,14)">
        <rect x="0" y="0" width="46" height="30" rx="10" style="fill:var(--cta)"/>
        <circle cx="12" cy="15" r="3" fill="#fff"/><circle cx="23" cy="15" r="3" fill="#fff"/><circle cx="34" cy="15" r="3" fill="#fff"/>
        <path d="M14 30 L8 40 L22 30 Z" style="fill:var(--cta)"/>
      </g>
    </svg>
    """
    st.markdown(
        '<div class="empty-state">'
        f'{_empty_svg}'
        f'<div class="empty-state-title">{_html.escape(T("empty_title"))}</div>'
        '<div class="empty-state-sub">One line per person as a header (e.g. "Alice:"), followed by bullet points — '
        'members, tasks and blockers are detected automatically.</div>'
        '</div>',
        unsafe_allow_html=True
    )

    # ── ONBOARDING WALKTHROUGH — a concrete 2-3 step example, shown
    # expanded automatically the first time this deployment is used (a
    # small local flag file, same persistence pattern as roster/presets),
    # then collapsed by default afterwards but still available to reopen. ──
    _onboarded = load_shared_settings().get("onboarded", False)
    with st.expander("New here? See a quick 3-step example", expanded=not _onboarded):
        st.markdown("""
**Step 1 — Paste one block per person.** Start each person's block with their name and a colon:
```
Priya:
- Fixed the login bug reported by QA.
- Blocked on staging access from DevOps.
```
**Step 2 — Add as many people as you like**, each with their own `- ` bullet lines underneath their name.

**Step 3 — Click \u201cGenerate Professional Status\u201d** below. SanghaStatus turns those raw notes into a
polished narrative, chat update, WhatsApp message, email, and more — all editable, all in one place.
""")
        if not _onboarded:
            save_shared_settings({"onboarded": True})


def _render_audience_tab(res: dict):
    """23: per-audience rewrites. One LLM call per button; results are stored in last_output so they
    survive reruns. The client version hides internal blockers and @mentions (prompt + deterministic filter)."""
    st.caption("One AI call per button, written from your current narrative. The client version hides internal blockers and @mentions.")
    _blk = [b for m in (res.get("members") or []) for b in m.get("blockers", [])]
    _cols = st.columns(3)
    for _col, (_k, (_label, _)) in zip(_cols, AUDIENCE_OPTIONS.items()):
        with _col:
            if st.button(_label, key=f"aud_{_k}", help=("Hides internal blockers and @mentions" if _k == "client" else None)):
                with st.spinner(f"Writing {_label.lower()}…"):
                    _txt, _toks, _err = audience_rewrite(_k, current_texts(res)["narrative"], _blk, mask=res.get("mask", False))
                if _err:
                    st.error(f"Couldn't write that version: {_err}")
                else:
                    res.setdefault("audience", {})[_k] = _txt
                    res["run_tokens"] = res.get("run_tokens", 0) + _toks
                    st.session_state.session_tokens += _toks
    _any = False
    for _k, (_label, _) in AUDIENCE_OPTIONS.items():
        _txt = (res.get("audience") or {}).get(_k)
        if _txt:
            _any = True
            st.markdown(f'<div class="eyebrow" style="margin-top:1rem;" role="heading" aria-level="3">{_html.escape(_label)}</div>', unsafe_allow_html=True)
            st.code(_txt, language="text")
    if not _any:
        st.caption("Nothing written yet — pick an audience above.")


def _render_week_tab(res: dict):
    """28: Friday roll-up of the last 7 days from saved history (deterministic) + optional LLM paragraph."""
    try:
        _base = date.fromisoformat(res.get("base_date") or date.today().isoformat())
    except Exception:
        _base = date.today()
    _w = week_stats(json.dumps(st.session_state.history, default=str), _base.isoformat(), load_sprint_goal())
    _title = "Friday roll-up" if _w["friday"] else "Last 7 days"
    st.markdown(
        f'<div class="eyebrow" role="heading" aria-level="3">{_title} · {_w["from"]} → {_w["to"]}</div>'
        f'<div class="stats-row"><div class="stat-chip"><div class="stat-val">{_w["standups"]}</div><div class="stat-lbl">Standups</div></div>'
        f'<div class="stat-chip"><div class="stat-val">{_w["tasks"]}</div><div class="stat-lbl">Tasks</div></div>'
        f'<div class="stat-chip"><div class="stat-val">{_w["blockers"]}</div><div class="stat-lbl">Blockers</div></div></div>',
        unsafe_allow_html=True)
    _txt = week_text(_w)
    st.code(_txt, language="text")
    _pk = f"week_para_{TEAM_SLUG}"
    if st.button("Add an AI summary paragraph (one AI call)", key="week_llm_btn"):
        with st.spinner("Summarising the week…"):
            _para, _toks, _err = week_llm_paragraph(_txt, mask=res.get("mask", False))
        if _err:
            st.error(f"Couldn't write the summary: {_err}")
        else:
            st.session_state[_pk] = _para
            st.session_state.session_tokens += _toks
    if st.session_state.get(_pk):
        st.markdown('<div class="eyebrow" style="margin-top:1rem;">AI summary</div>', unsafe_allow_html=True)
        st.code(st.session_state[_pk], language="text")


def render_output(res):
    """Render the generated-output section purely from a stored result dict.
    No LLM/DB/history writes happen here, so it is safe to call on every rerun."""
    data       = res["data"]
    fmt_date   = res["fmt_date"]
    narrative  = res["narrative"]
    chat       = res["chat"]
    wa         = res["wa"]
    email_raw  = res["email_raw"]
    lines      = email_raw.splitlines()
    subj_line  = next((l for l in lines if l.lower().startswith("subject:")), "")
    subj       = subj_line.replace("Subject:", "").replace("subject:", "").strip()
    body_lines = [l for l in lines if l != subj_line]
    body_text  = "\n".join(body_lines).strip()
    mailto     = mailto_link(subj, body_text)
    tpl        = TEMPLATES.get(res.get("template", "Standup"), TEMPLATES["Standup"])

    # ── TABBED OUTPUT PANEL — all generated formats switch via
    # st.tabs() instead of stacking every card down the page; all
    # existing functionality (copy buttons, editable text areas,
    # download/mailto links, Slack send) is preserved inside each
    # tab, unchanged. ──
    jira_markup = to_jira_confluence_markup(chat)
    teams_markup = to_teams_markup(chat)
    discord_markup = to_discord_markup(chat)

    # On the first render after a fresh generation, overwrite any text edits / ticked
    # checkboxes left over from the PREVIOUS output; afterwards (reruns) leave them alone.
    _fresh = res.pop("fresh", False)
    _refresh = res.pop("refresh_edits", False)       # revise / version-restore: reset text edits but keep ticked action items
    if _fresh or _refresh:
        for _k, _v in (("edit_narrative", narrative), ("edit_chat", chat), ("edit_whatsapp", wa),
                       ("edit_jira", jira_markup), ("edit_teams", teams_markup),
                       ("edit_discord", discord_markup), ("edit_email", email_raw)):
            st.session_state[_k] = _v
    if _fresh:
        for _k in [k for k in st.session_state.keys() if isinstance(k, str) and k.startswith("action_item_")]:
            st.session_state[_k] = False
    for _k, _v in (("edit_narrative", narrative), ("edit_chat", chat), ("edit_whatsapp", wa),
                   ("edit_jira", jira_markup), ("edit_teams", teams_markup),
                   ("edit_discord", discord_markup), ("edit_email", email_raw)):
        st.session_state.setdefault(_k, _v)

    _tab_labels = [tpl["tab_narrative"], "Chat", "WhatsApp", "Jira/Confluence", "Teams", "Discord", "Email"]
    _show_tomorrow = bool(res["include_tomorrow"] and data.get("tomorrow_plan"))
    _show_blockers = bool((res["include_blockers"] and data.get("blocker_summary")) or res.get("blocker_meta"))
    if _show_tomorrow:
        _tab_labels.append(tpl["tab_tomorrow"])
    if _show_blockers:
        _tab_labels.append(tpl["tab_blockers"])
    _tab_labels += ["Audience", "Week"]

    # 24: "By the numbers" strip (deterministic, from the notes) above the tabs
    if res.get("metrics"):
        _chips = "".join(f'<span class="ns-chip"><b>{n}</b> {_html.escape(l)}</span>' for l, n in res["metrics"][:6])
        st.markdown(f'<div class="numbers-strip" role="group" aria-label="By the numbers"><span class="ns-label">By the numbers</span>{_chips}</div>',
                    unsafe_allow_html=True)
    _tabs = st.tabs(_tab_labels)
    _tab_iter = iter(_tabs)

    with next(_tab_iter):
        st.markdown(
            '<div class="colored-block narrative-block">'
            '<div class="block-title narrative-title"><span class="block-title-text"><span class="block-icon-badge"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 6h16M4 10h12M4 14h16M4 18h10"/></svg></span>' + _html.escape(tpl["narr_title"]) + '</span></div>',
            unsafe_allow_html=True
        )
        st.text_area("Narrative", height=dynamic_ta_height(narrative), key="edit_narrative", label_visibility="collapsed")
        render_copy_button(narrative, "narrative")

    with next(_tab_iter):
        st.markdown(
            '<div class="colored-block chat-block">'
            '<div class="block-title chat-title"><span class="block-title-text"><span class="block-icon-badge"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M21 12a8 8 0 0 1-11.6 7.1L4 20l1-4.6A8 8 0 1 1 21 12z"/></svg></span>Chat Update (Slack / Teams)</span></div>',
            unsafe_allow_html=True
        )
        st.text_area("Chat", height=dynamic_ta_height(chat), key="edit_chat", label_visibility="collapsed")
        render_copy_button(chat, "chat")
        # SKIPPED: a real Slack/Teams BOT that auto-pulls updates and posts back
        # on its own needs a registered Slack app + bot token/credentials this
        # codebase doesn't have — the webhook send below is the achievable version.
        # SKIPPED: real Jira/Linear LIVE ticket sync needs API credentials not
        # available here; to_jira_confluence_markup() above covers copy/paste.
        # SKIPPED: scheduled/unattended auto-generation + auto-post isn't possible —
        # this is a single Streamlit Cloud app opened in a browser by whoever runs
        # standup; there is no background/cron process available to it (same
        # reasoning as the sister app).
        with st.expander("Send directly to Slack", expanded=False):
            st.caption(
                "Paste your Slack **Incoming Webhook URL** (Slack → Apps → Incoming Webhooks) — "
                "it's used once for this send and isn't stored anywhere."
            )
            slack_webhook_url = st.text_input(
                "Slack Webhook URL", placeholder="https://hooks.slack.com/services/…",
                key="slack_webhook_url", type="password", label_visibility="collapsed"
            )
            if st.button("Send to Slack", key="send_slack_btn"):
                if not slack_webhook_url.strip():
                    st.warning("Paste a webhook URL first.")
                elif not slack_webhook_url.startswith("https://hooks.slack.com/"):
                    st.warning("That doesn't look like a Slack webhook URL (should start with https://hooks.slack.com/…).")
                else:
                    try:
                        import requests as _requests
                        resp = _requests.post(
                            slack_webhook_url.strip(),
                            json={"text": st.session_state.get("edit_chat", chat)},
                            timeout=8
                        )
                        if resp.status_code == 200:
                            _notify("Sent to Slack")
                        else:
                            st.error(f"Slack responded with {resp.status_code}: {resp.text[:200]}")
                    except Exception as e:
                        st.error(f"Couldn't reach Slack: {e}")

    with next(_tab_iter):
        st.markdown(
            '<div class="colored-block whatsapp-block">'
            '<div class="block-title whatsapp-title"><span class="block-title-text"><span class="block-icon-badge"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M7 3h10a1 1 0 0 1 1 1v16a1 1 0 0 1-1 1H7a1 1 0 0 1-1-1V4a1 1 0 0 1 1-1zM11 18h2"/></svg></span>WhatsApp Update</span></div>',
            unsafe_allow_html=True
        )
        st.text_area("WhatsApp", height=dynamic_ta_height(wa), key="edit_whatsapp", label_visibility="collapsed")
        render_copy_button(wa, "whatsapp")

    with next(_tab_iter):
        # Jira/Confluence markup — derived instantly from chat_update, no extra API call
        st.markdown(
            '<div class="colored-block tomorrow-block">'
            '<div class="block-title tomorrow-title"><span class="block-title-text"><span class="block-icon-badge"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 3 3 8l9 5 9-5-9-5zM3 13l9 5 9-5"/></svg></span>Jira / Confluence Markup</span></div>',
            unsafe_allow_html=True
        )
        st.text_area("Jira", height=dynamic_ta_height(jira_markup), key="edit_jira", label_visibility="collapsed")
        render_copy_button(jira_markup, "jira")

    with next(_tab_iter):
        st.markdown(
            '<div class="colored-block tomorrow-block">'
            '<div class="block-title tomorrow-title"><span class="block-title-text"><span class="block-icon-badge"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M16 20v-1a4 4 0 0 0-4-4H7a4 4 0 0 0-4 4v1M9.5 11a3.5 3.5 0 1 0 0-7 3.5 3.5 0 0 0 0 7zM21 20v-1a4 4 0 0 0-3-3.9M16 4.1a3.5 3.5 0 0 1 0 6.8"/></svg></span>Teams Format</span></div>',
            unsafe_allow_html=True
        )
        st.text_area("Teams", height=dynamic_ta_height(teams_markup), key="edit_teams", label_visibility="collapsed")
        render_copy_button(teams_markup, "teams")

    with next(_tab_iter):
        st.markdown(
            '<div class="colored-block tomorrow-block">'
            '<div class="block-title tomorrow-title"><span class="block-title-text"><span class="block-icon-badge"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M5 9h14M5 15h14M10 4 8 20M16 4l-2 16"/></svg></span>Discord Format</span></div>',
            unsafe_allow_html=True
        )
        st.text_area("Discord", height=dynamic_ta_height(discord_markup), key="edit_discord", label_visibility="collapsed")
        render_copy_button(discord_markup, "discord")

    with next(_tab_iter):
        # Email — with mailto button
        st.markdown(
            f'<div class="colored-block email-block">'
            f'<div class="block-title email-title">'
            f'<span class="block-title-text"><span class="block-icon-badge"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 6h16a1 1 0 0 1 1 1v10a1 1 0 0 1-1 1H4a1 1 0 0 1-1-1V7a1 1 0 0 1 1-1zM3 7l9 6 9-6"/></svg></span>Email Update</span>'
            f'<a class="action-btn" href="{mailto}">Open in Mail app</a></div>',
            unsafe_allow_html=True
        )
        st.text_area("Email", height=dynamic_ta_height(email_raw), key="edit_email", label_visibility="collapsed")
        render_copy_button(email_raw, "email")

    if _show_tomorrow:
        with next(_tab_iter):
            st.markdown(
                '<div class="colored-block tomorrow-block">'
                '<div class="block-title tomorrow-title"><span class="block-title-text"><span class="block-icon-badge"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M5 6h14a1 1 0 0 1 1 1v12a1 1 0 0 1-1 1H5a1 1 0 0 1-1-1V7a1 1 0 0 1 1-1zM4 10h16M8 3v4M16 3v4"/></svg></span>' + _html.escape(tpl["tomorrow_title"]) + '</span></div>',
                unsafe_allow_html=True
            )
            st.code(data["tomorrow_plan"], language="text")

    if _show_blockers:
        with next(_tab_iter):
            st.markdown(
                '<div class="colored-block blocker-block">'
                '<div class="block-title blocker-title"><span class="block-title-text"><span class="block-icon-badge"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 3 2 20h20L12 3zM12 10v4M12 17h.01"/></svg></span>' + _html.escape(tpl["blockers_title"]) + '</span></div>',
                unsafe_allow_html=True
            )
            if data.get("blocker_summary"):
                st.code(data["blocker_summary"], language="text")
            _mrows = _meta_rows(res)
            if _mrows:
                st.markdown(
                    '<table class="bk-table"><caption class="sr-only">Blocker owners and needed-by dates</caption><thead><tr><th>Person</th><th>Blocker</th><th>Owner</th><th>Needed by</th></tr></thead><tbody>'
                    + "".join(f"<tr><td>{_html.escape(a)}</td><td>\u25b2 {_html.escape(b)}</td><td>{_html.escape(c)}</td><td>{_html.escape(d)}</td></tr>" for a, b, c, d in _mrows)
                    + "</tbody></table>", unsafe_allow_html=True)

    # ── Audience + Week tabs (always the last two) ──
    with next(_tab_iter):
        _render_audience_tab(res)
    with next(_tab_iter):
        _render_week_tab(res)

    run_tokens = res["run_tokens"]
    st.markdown(
        f'<div class="token-row"><div class="token-badge">'
        f'This run: {run_tokens:,} tokens &nbsp;·&nbsp; '
        f'Session total: {st.session_state.session_tokens:,} tokens &nbsp;·&nbsp; '
        f'Runs saved: {len(st.session_state.history)}</div></div>',
        unsafe_allow_html=True
    )

    # ── 21: edit-after-generate loop — revise the CURRENT stored output (not the raw notes) ──
    st.markdown(f'<div class="eyebrow" style="margin-top:1.25rem;" role="heading" aria-level="3">{_html.escape(T("refine"))}</div>', unsafe_allow_html=True)
    _rv_cols = st.columns(4)
    for _col, (_rk, (_rlabel, _)) in zip(_rv_cols, REVISE_OPTIONS.items()):
        with _col:
            if st.button(_rlabel, key=f"rev_{_rk}"):
                _t = current_texts(res)
                _fields = {"standup_narrative": _t["narrative"], "chat_update": _t["chat"],
                           "whatsapp_update": _t["wa"], "email_update": _t["email"]}
                if _t["tomorrow"]:
                    _fields["tomorrow_plan"] = _t["tomorrow"]
                if _t["blockers"]:
                    _fields["blocker_summary"] = _t["blockers"]
                with st.spinner(f"Making it {_rlabel.lower()}…"):
                    _new, _toks, _err = revise_output(_fields, _rk, mask=res.get("mask", False))
                if _err or not _new:
                    st.error(f"Couldn't revise: {_err or 'no result'}. Your current output is unchanged.")
                else:
                    res["data"] = {**res["data"], **_new}
                    res["narrative"] = _new.get("standup_narrative", res["narrative"])
                    res["chat"] = _new.get("chat_update", res["chat"])
                    res["wa"] = _new.get("whatsapp_update", res["wa"])
                    res["email_raw"] = _new.get("email_update", res["email_raw"])
                    res["versions"] = ((res.get("versions") or []) + [_make_version_snapshot(res, _rlabel)])[-3:]
                    res["refresh_edits"] = True
                    res["run_tokens"] = res.get("run_tokens", 0) + _toks
                    st.session_state.session_tokens += _toks
                    _persist_output_to_history(res)
                    st.session_state.pop("ver_pick", None)
                    _notify_next_run(f"Updated: {_rlabel}")
                    st.rerun()

    # ── 36: version history (last 3) ──
    _vers = res.get("versions") or []
    if len(_vers) > 1:
        _vlabels = [f"v{v['n']} · {v['label']} · {v['ts']}" for v in reversed(_vers)]
        _vc1, _vc2 = st.columns([3, 1])
        with _vc1:
            _vpick = st.selectbox("Versions", _vlabels, key="ver_pick")
        with _vc2:
            st.write("")
            if st.button("Restore", key="ver_restore_btn"):
                _apply_snapshot(res, _vers[len(_vers) - 1 - _vlabels.index(_vpick)])
                _persist_output_to_history(res)
                _notify_next_run(f"Restored {_vpick.split(' · ')[0]}")
                st.rerun()

    # ── 22: consistency check card (deterministic) ──
    if res.get("members"):
        _t = current_texts(res)
        _chk = _cached_consistency(json.dumps(res["members"]), json.dumps([_t["narrative"], _t["chat"], _t["wa"], _t["email"]]))
        _ok = not _chk["missing"] and not _chk["unsupported"]
        _glyph = "✓" if _ok else "⚠"
        _body = ""
        if _ok:
            _body = f"Every one of the {_chk['tasks']} tasks in your notes appears in the output, and every output sentence traces back to your notes."
        else:
            if _chk["missing"]:
                _body += f'<div class="chk-h">Tasks in your notes that seem missing from the output ({len(_chk["missing"])})</div><ul>' + "".join(
                    f"<li><b>{_html.escape(n)}</b>: {_html.escape(t)}</li>" for n, t in _chk["missing"][:6]) + "</ul>"
            if _chk["unsupported"]:
                _body += f'<div class="chk-h">Output sentences with no source in your notes ({len(_chk["unsupported"])})</div><ul>' + "".join(
                    f"<li>{_html.escape(x)}</li>" for x in _chk["unsupported"][:6]) + "</ul>"
        st.markdown(
            f'<div class="hint-card {"ok" if _ok else "warn"} check-card" role="note"><div class="hint-title"><span class="glyph" aria-hidden="true">{_glyph}</span> '
            f'Check — notes vs. output <span class="chk-sub">(fuzzy text match, no AI)</span></div>{_body}</div>',
            unsafe_allow_html=True)

    # ── downloads: docx / pdf / md / html ──
    _brand_project = (st.session_state.get("pref_brand_project", "") or res.get("project", "")).strip()
    _logo = load_logo()
    _logo_bytes = _logo[1] if _logo else b""
    dl1, dl2, dl3, dl4 = st.columns(4)
    with dl1:
        docx_bytes, docx_err = _cached_docx(json.dumps(data, default=str), fmt_date, res["prepared_by"], res.get("template", "Standup"),
                                             json.dumps(res.get("blocker_meta") or []), _brand_project)
        if docx_bytes:
            _dl_button(
                "Download Word (.docx)", data=docx_bytes,
                file_name=f"status_{date.today().isoformat()}.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                key="dl_docx"
            )
        elif docx_err:
            st.caption(f"Word export unavailable: {docx_err}")
    with dl2:
        pdf_bytes, pdf_err = _cached_pdf(json.dumps(data, default=str), fmt_date, res["prepared_by"], _brand_project, _logo_bytes,
                                         res.get("template", "Standup"), json.dumps(res.get("blocker_meta") or []))
        if pdf_bytes:
            _dl_button(
                "Download PDF", data=pdf_bytes,
                file_name=f"status_{date.today().isoformat()}.pdf",
                mime="application/pdf", key="dl_pdf"
            )
        elif pdf_err:
            st.caption(f"PDF export unavailable: {pdf_err}")
    with dl3:
        _dl_button("Download Markdown (.md)", data=build_markdown_export(res), file_name=f"status_{date.today().isoformat()}.md",
                   mime="text/markdown", key="dl_md")
    with dl4:
        _dl_button("Download HTML (.html)", data=build_html_export(res), file_name=f"status_{date.today().isoformat()}.html",
                   mime="text/html", key="dl_html")

    # ── 33: formatted clipboard copies (rich text + plain-text fallback) ──
    _md_now = build_markdown_export(res)
    _cp1, _cp2, _cp3 = st.columns([1, 1, 2])
    with _cp1:
        render_copy_button(_md_now, "confluence", "Copy for Confluence", html=simple_md_to_html(_md_now))
    with _cp2:
        render_copy_button(_md_now, "notion", "Copy for Notion", html=simple_md_to_html(_md_now))

    # ── ACTION ITEMS — regex-extracted "will [X] by [when]" phrases from the raw updates (+ 25: concrete dates) ──
    _action_items = res["action_items"]
    _followthrough = res["followthrough"]
    if _followthrough:
        st.markdown(
            '<div class="colored-block tomorrow-block">'
            '<div class="block-title tomorrow-title" role="heading" aria-level="3"><span class="block-title-text">'
            '<span class="block-icon-badge"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M17 2l4 4-4 4M3 11V9a3 3 0 0 1 3-3h15M7 22l-4-4 4-4M21 13v2a3 3 0 0 1-3 3H3"/></svg></span>Yesterday\'s Action Items — Follow-through</span></div>',
            unsafe_allow_html=True
        )
        for _ft in _followthrough:
            _status = "✓ appears done" if _ft["done"] else "○ still open"
            st.markdown(f"- **{_ft['name']}** — {_ft['text']} (was due {_ft['when']}) — {_status}")
        st.caption("Heuristic fuzzy text match against today's tasks — not a verified completion.")
    if _action_items or res.get("dated"):
        st.markdown(
            '<div class="colored-block tomorrow-block">'
            '<div class="block-title tomorrow-title" role="heading" aria-level="3"><span class="block-title-text">'
            '<span class="block-icon-badge"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M9 12l2 2 4-4M12 21a9 9 0 1 0 0-18 9 9 0 0 0 0 18z"/></svg></span>Action Items</span></div>',
            unsafe_allow_html=True
        )
        for _ai_idx, _ai in enumerate(_action_items):
            _dtxt = ""
            if _ai.get("date"):
                try:
                    _dtxt = f" → {fmt_short_date(date.fromisoformat(_ai['date']))}"
                except Exception:
                    pass
            st.checkbox(
                f"**{_ai['name']}** — {_ai['text']} (by {_ai['when']}{_dtxt})",
                key=f"action_item_{_ai_idx}_{hashlib.md5(_ai['text'].encode()).hexdigest()[:8]}"
            )
        _ai_texts = {a["text"] for a in _action_items}
        _extra = [d for d in (res.get("dated") or []) if not any(t and t in d["text"] for t in _ai_texts)]
        if _extra:
            st.caption("Other dates mentioned in the notes, resolved against the standup date:")
            for _d in _extra:
                try:
                    st.markdown(f"- **{_d['name']}** — {_d['text']} → *{_d['phrase']}* = **{fmt_short_date(date.fromisoformat(_d['date']))}**")
                except Exception:
                    pass


# ═══════════════════════════════════════════════════
# GENERATE
# ═══════════════════════════════════════════════════
generate = st.button(T("generate"), key="generate_btn", type="primary")

if generate:
    if not raw_updates.strip():
        st.warning("Please paste your team's raw updates first.")
    elif not members:
        st.warning("Could not detect any team member names. Use 'Name:' format.")
    else:
        st.session_state.pop("last_output", None)
        slot = st.empty()
        slot.markdown(render_loader(0), unsafe_allow_html=True)

        try:
            fmt_date    = standup_date.strftime("%B %d, %Y")
            project_tag = f" | {project_name}" if project_name.strip() else ""
            tone_instr  = TONE_OPTIONS[tone_choice]
            domain_str  = DOMAIN_OPTIONS[domain_choice]
            lang_str    = OUTPUT_LANG_OPTIONS[lang_choice]

            # 35: mask secrets/PII in the PROMPT PAYLOAD only (stored raw notes stay untouched).
            _payload_raw = mask_sensitive(_effective_raw)[0] if (_scrub_found and st.session_state.get("scrub_mask", True)) else _effective_raw
            _blocker_meta = _collect_blocker_meta(members, standup_date)
            _blocker_meta_note = blocker_meta_prompt(_blocker_meta)
            _tpl = st.session_state.get("pref_template", "Standup")
            _out_today_now = st.session_state.get("out_today_members", [])
            _out_today_note = (
                f"\nOut today (do not schedule new tasks for them tomorrow; mention briefly if relevant): "
                f"{', '.join(_out_today_now)}.\n" if _out_today_now else ""
            )
            prompt_payload = f"""
Use this date for all sections: {fmt_date}
Project/Sprint: {project_name or "General"}
Team Members detected: {len(members)} ({', '.join(m['name'] for m in members)})
{_out_today_note}{_blocker_meta_note}
Raw Updates:
{_payload_raw}

Embed the project tag "{project_tag}" in the chat_update header and email subject line.
"""
            if _scrub_found and st.session_state.get("scrub_mask", True):
                prompt_payload = mask_sensitive(prompt_payload)[0]      # 35: everything that leaves the app is masked, incl. blocker notes
            _glossary_block = glossary_prompt_block(load_glossary())
            narrative_prompt = build_narrative_prompt(tone_instr, domain_str, lang_str, include_tomorrow, include_blockers, _glossary_block, template=_tpl)
            chat_prompt       = build_chat_prompt(tone_instr, domain_str, lang_str, _glossary_block, template=_tpl)
            email_prompt      = build_email_prompt(tone_instr, domain_str, lang_str, _glossary_block, template=_tpl)

            slot.markdown(render_loader(1), unsafe_allow_html=True)

            # Scale token budgets by team size — a 1-person update needs far
            # fewer tokens than a 10-person one; fixed budgets either waste
            # headroom (small teams) or truncate (large teams).
            team_size = max(1, len(members))
            narrative_tokens = min(3000, 900 + team_size * 220)
            chat_tokens       = min(2600, 800 + team_size * 180)
            email_tokens      = min(2200, 700 + team_size * 160)

            # ── THREE INDEPENDENT CALLS IN PARALLEL ──
            # Narrative, chat/WhatsApp, and email don't depend on each other,
            # so firing them concurrently cuts total wait time to roughly the
            # slowest single call instead of the sum of all three.
            total_tokens_used = 0
            with ThreadPoolExecutor(max_workers=3) as ex:
                fut_narrative = ex.submit(call_llm_json, narrative_prompt, prompt_payload, 0.1, narrative_tokens)
                fut_chat      = ex.submit(call_llm_json, chat_prompt, prompt_payload, 0.1, chat_tokens)
                fut_email     = ex.submit(call_llm_json, email_prompt, prompt_payload, 0.1, email_tokens)

                results = {}
                errors  = {}
                for name, fut in (("narrative", fut_narrative), ("chat", fut_chat), ("email", fut_email)):
                    try:
                        piece, completion = fut.result()
                        results[name] = piece
                        if hasattr(completion, "usage") and completion.usage:
                            total_tokens_used += completion.usage.total_tokens
                    except Exception as e:
                        errors[name] = e

                # Retry only the piece(s) that actually failed, not all three —
                # cheaper and faster than a blanket full retry.
                retry_prompts = {
                    "narrative": (narrative_prompt, narrative_tokens),
                    "chat":      (chat_prompt, chat_tokens),
                    "email":     (email_prompt, email_tokens),
                }
                for name in list(errors.keys()):
                    p, budget = retry_prompts[name]
                    try:
                        piece, completion = call_llm_json(p, prompt_payload, 0.05, budget)
                        results[name] = piece
                        if hasattr(completion, "usage") and completion.usage:
                            total_tokens_used += completion.usage.total_tokens
                        del errors[name]
                    except Exception:
                        pass  # still failed after retry — that piece just won't render

                data = {}
                for piece in results.values():
                    data.update(piece)

                if errors:
                    st.warning(f"⚠️ Could not generate: {', '.join(errors.keys())}. Try regenerating.")

            slot.markdown(render_loader(2), unsafe_allow_html=True)

            st.session_state.session_tokens += total_tokens_used

            # Capture yesterday's entry (if any) BEFORE inserting today's,
            # so we can diff today's tasks against it.
            previous_entry = st.session_state.history[0] if st.session_state.history else None

            _saved_at_now = datetime.now().isoformat()
            if _blocker_meta:
                data["blocker_meta"] = _blocker_meta      # 27: persisted with the history entry
            data["template"] = _tpl
            st.session_state.history.insert(0, {
                "date": fmt_date, "project": project_name or "—",
                "members": len(members), "tasks": sum(m["count"] for m in members),
                "tone": tone_choice, "domain": domain_choice, "lang": lang_choice,
                "data": data, "members_detail": members,
                "saved_at": _saved_at_now,
            })
            st.session_state.history = st.session_state.history[:MAX_HISTORY]
            save_history_to_disk(st.session_state.history)

            slot.empty()
            st.markdown("<br>", unsafe_allow_html=True)

            narrative = data.get("standup_narrative", "")
            chat      = data.get("chat_update", "")
            wa        = data.get("whatsapp_update", "")
            email_raw = data.get("email_update", "")

            # Append the optional quick team question, if one was typed —
            # a deterministic footer, not something the LLM was asked about.
            _qq = st.session_state.get("quick_poll_question", "").strip()
            if _qq:
                chat = chat.rstrip() + f"\n\n💬 Quick question: {_qq}"
                wa   = wa.rstrip() + f"\n\n💬 Quick question: {_qq}"

            # Store everything the output section needs; it is rendered from
            # session state on EVERY run (see below), not only on this click.
            st.session_state["last_output"] = {
                "team_slug": TEAM_SLUG, "fresh": True, "data": data, "fmt_date": fmt_date,
                "narrative": narrative, "chat": chat, "wa": wa, "email_raw": email_raw,
                "include_tomorrow": include_tomorrow, "include_blockers": include_blockers,
                "prepared_by": your_name.strip(),
                "run_tokens": total_tokens_used,
                "action_items": resolve_action_dates(extract_action_items(members), standup_date),
                "followthrough": check_action_item_followthrough(members, [previous_entry] if previous_entry else []),
                # ── ITERATION A/B additions: everything the output panel needs lives in stored state ──
                "members": members, "saved_at": _saved_at_now, "base_date": standup_date.isoformat(),
                "metrics": extract_metrics(members),
                "dated": extract_dated_mentions(members, standup_date),
                "template": _tpl, "blocker_meta": _blocker_meta, "project": project_name.strip(),
                "audience": {}, "mask": bool(_scrub_found and st.session_state.get("scrub_mask", True)),
            }
            st.session_state["last_output"]["versions"] = [_make_version_snapshot(st.session_state["last_output"], "Generated")]


        except json.JSONDecodeError:
            slot.empty()
            st.warning("Malformed response \u2014 retrying once\u2026")
            try:
                with ThreadPoolExecutor(max_workers=3) as ex:
                    fut_n = ex.submit(call_llm_json, narrative_prompt, prompt_payload, 0.05, 1600)
                    fut_c = ex.submit(call_llm_json, chat_prompt, prompt_payload, 0.05, 1400)
                    fut_e = ex.submit(call_llm_json, email_prompt, prompt_payload, 0.05, 1200)
                    data2 = {}
                    for fut in (fut_n, fut_c, fut_e):
                        piece, _ = fut.result()
                        data2.update(piece)
                _notify("Retry succeeded")
                st.code(data2.get("standup_narrative", ""), language="text")
            except Exception:
                st.error("Both attempts failed. Please try again.")
        except Exception as e:
            slot.empty()
            st.error(f"Something went wrong: {e}")

# Render the stored output on every run (survives widget-triggered reruns).
_lo = st.session_state.get("last_output")
if _lo and _lo.get("team_slug") != TEAM_SLUG:
    st.session_state.pop("last_output", None)
    _lo = None
if _lo:
    render_output(_lo)
    if st.button(T("clear_output"), key="sec_clear_output_btn"):
        st.session_state.pop("last_output", None)
        st.rerun()


# ═══════════════════════════════════════════════════
# HISTORY
# ═══════════════════════════════════════════════════
if st.session_state.history:
    st.markdown(
        f'<hr class="divider"><div class="section-head" style="margin-top:3rem;"><div class="eyebrow">{_html.escape(T("history"))}</div>'
        f'<h2>{_html.escape(T("past_standups"))}</h2><p>Every saved update, newest first \u2014 replay, filter and export.</p></div>',
        unsafe_allow_html=True
    )

    # ── VISUAL TIMELINE — dots + connecting line, newest first, as an
    # at-a-glance overview before drilling into any single entry below. ──
    _tl_dots = "".join(
        f'<div class="tl-node">'
        f'<div class="tl-dot" title="{e["date"]}"></div>'
        f'<div class="tl-label">{e["date"].split(" · ")[0]}</div>'
        f'<div class="tl-sub">{e.get("tasks", 0)} tasks</div>'
        f'</div>'
        for e in st.session_state.history
    )
    st.markdown(
        f'<div class="timeline-wrap reveal"><div class="timeline-line"></div>{_tl_dots}</div>',
        unsafe_allow_html=True
    )

    with st.expander(f"Past standups ({len(st.session_state.history)} saved) \u2014 expand & replay", expanded=False):
        _hist_filter = st.text_input(
            "Filter by member name or keyword in their tasks/blockers",
            placeholder="e.g. Alice, or 'payment gateway'", key="hist_filter_text"
        )

        def _entry_matches_filter(entry, needle):
            if not needle:
                return True
            needle = needle.lower()
            if needle in entry.get("project", "").lower() or needle in entry.get("date", "").lower():
                return True
            for m in entry.get("members_detail", []):
                if needle in m["name"].lower():
                    return True
                if any(needle in t.lower() for t in m.get("tasks", [])):
                    return True
                if any(needle in b.lower() for b in m.get("blockers", [])):
                    return True
            return False

        _filtered_history = [e for e in st.session_state.history if _entry_matches_filter(e, _hist_filter)]
        if _hist_filter and not _filtered_history:
            st.caption("No saved standups match that filter.")
        for idx, entry in enumerate(_filtered_history):
            st.markdown(
                f'<div class="hist-card"><div>'
                f'<div class="hist-date">{entry["date"]} &nbsp;\u00b7&nbsp; {entry.get("project","—")}</div>'
                f'<div class="hist-meta">{entry["members"]} members &nbsp;\u00b7&nbsp; {entry["tasks"]} tasks '
                f'&nbsp;·&nbsp; {entry["tone"]} &nbsp;·&nbsp; {entry["domain"]} &nbsp;·&nbsp; {entry["lang"]}</div>'
                f'</div></div>',
                unsafe_allow_html=True
            )
            with _sub_expander(f"View outputs — {entry['date']}", expanded=False):
                d = entry["data"]
                st.markdown("**Narrative**")
                st.code(d.get("standup_narrative", ""), language="text")
                st.markdown("**Chat**")
                st.code(d.get("chat_update", ""), language="text")
                st.markdown("**WhatsApp**")
                st.code(d.get("whatsapp_update", ""), language="text")
                st.markdown("**Email**")
                st.code(d.get("email_update", ""), language="text")
                if d.get("tomorrow_plan"):
                    st.markdown("**Tomorrow**")
                    st.code(d["tomorrow_plan"], language="text")
                if d.get("blocker_summary"):
                    st.markdown("**Blockers**")
                    st.code(d["blocker_summary"], language="text")

        # ── CSV EXPORT — date, member count, total tasks, total blockers,
        # health score (recomputed per entry from that entry's own blocker
        # signal — an approximation, since the true cross-entry escalation
        # history isn't reconstructable snapshot-by-snapshot at export time). ──
        import csv as _csv
        import io as _csv_io
        _csv_buf = _csv_io.StringIO()
        _csv_writer = _csv.writer(_csv_buf)
        _csv_writer.writerow(["Date", "Project", "Members", "Total Tasks", "Total Blockers", "Health Score", "Health Label"])
        for _e in st.session_state.history:
            _e_members = _e.get("members_detail", [])
            _e_blockers = sum(len(m.get("blockers", [])) for m in _e_members)
            _e_score, _e_label = compute_health_score(_e_members, {}, {})
            _csv_writer.writerow([
                _e.get("date", ""), _e.get("project", ""), _e.get("members", 0),
                _e.get("tasks", 0), _e_blockers, _e_score, _e_label,
            ])
        st.download_button(
            "Download history as CSV", data=_csv_buf.getvalue(),
            file_name=f"sanghastatus_history_{TEAM_SLUG}.csv", mime="text/csv",
            key="sec_dl_history_csv"
        )

        if st.button("Clear all history", key="clear_hist"):
            st.session_state.history = []
            save_history_to_disk(st.session_state.history)
            st.rerun()

    # ── TEAM VELOCITY CHART — tasks reported per saved update, chronological ──
    if len(st.session_state.history) >= 2:
        import pandas as pd
        chron = list(reversed(st.session_state.history))  # oldest first for the chart
        chart_df = pd.DataFrame({
            "Date":  [e["date"] for e in chron],
            "Tasks": [e.get("tasks", 0) for e in chron],
        }).set_index("Date")
        st.markdown(
            '<div class="eyebrow" style="margin:2rem 0 0.5rem;">Team velocity \u00b7 tasks per saved update</div>',
            unsafe_allow_html=True
        )
        st.line_chart(chart_df, height=200)
        st.download_button(
            "Download velocity data (.csv)",
            data=chart_df.reset_index().to_csv(index=False),
            file_name="team_velocity.csv", mime="text/csv",
            key="dl_velocity_csv"
        )

        # ── PER-PERSON TREND VIEW — expands the brevity flag into a full
        # per-member chart (task count + avg words/task across saved runs),
        # so a manager can see one person's pattern over time, not just
        # today's single-run flag.
        all_names = sorted({
            m["name"] for e in st.session_state.history
            for m in e.get("members_detail", [])
        })
        if all_names:
            with _sub_expander("Per-person trend view", expanded=False):
                picked_member = st.selectbox("Team member", options=all_names, key="trend_member_pick")
                rows = []
                for e in chron:
                    match = next((m for m in e.get("members_detail", []) if m["name"] == picked_member), None)
                    if match:
                        n_tasks = len(match["tasks"])
                        avg_words = round(sum(len(t.split()) for t in match["tasks"]) / n_tasks, 1) if n_tasks else 0
                        rows.append({"Date": e["date"], "Tasks": n_tasks, "Avg words/task": avg_words})
                if len(rows) >= 2:
                    trend_df = pd.DataFrame(rows).set_index("Date")
                    st.line_chart(trend_df, height=200)
                    st.caption(f"{picked_member} appears in {len(rows)} of {len(st.session_state.history)} saved updates.")
                    st.download_button(
                        f"Download {picked_member}'s trend data (.csv)",
                        data=trend_df.reset_index().to_csv(index=False),
                        file_name=f"{picked_member.lower().replace(' ', '_')}_trend.csv", mime="text/csv",
                        key="dl_trend_csv"
                    )
                else:
                    st.caption(f"Not enough saved history for {picked_member} yet — need at least 2 updates mentioning them.")

    # ── WEEKLY ROLLUP — aggregates whatever's currently saved in history ──
    if len(st.session_state.history) >= 2:
        if st.button("Generate weekly rollup", key="weekly_rollup_btn"):
            rollup_lines = ["WEEKLY ROLLUP", "=" * 40, ""]
            person_totals = {}
            for entry in st.session_state.history:
                rollup_lines.append(f"📅 {entry['date']} — {entry.get('project','—')}")
                narrative = entry["data"].get("standup_narrative", "")
                rollup_lines.append(narrative)
                rollup_lines.append("-" * 30)
                person_totals[entry.get("project", "—")] = person_totals.get(entry.get("project", "—"), 0) + entry.get("tasks", 0)
            rollup_lines.append("")
            rollup_lines.append(f"Total standups included: {len(st.session_state.history)}")
            rollup_lines.append(f"Total tasks across all entries: {sum(e.get('tasks',0) for e in st.session_state.history)}")
            rollup_text = "\n".join(rollup_lines)
            st.markdown(
                '<div class="colored-block narrative-block">'
                '<div class="block-title narrative-title"><span class="block-title-text"><span class="block-icon-badge"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M5 21V10M12 21V4M19 21v-7"/></svg></span>Weekly Rollup</span></div>',
                unsafe_allow_html=True
            )
            st.code(rollup_text, language="text")
            st.download_button("Download rollup", data=rollup_text,
                              file_name=f"weekly_rollup_{date.today().isoformat()}.txt",
                              mime="text/plain", key="dl_rollup")

    # ── RETRO-READY EXPORT — aggregates ALL saved history entries into a
    # single 'Sprint Retro' text export: total tasks, total blockers, and
    # recurring themes (simple frequency count, no AI call). Deterministic
    # transform, same pattern as to_jira_confluence_markup() etc. ──
    if st.session_state.history:
        if st.button("Build sprint retro export", key="sec_retro_export_btn"):
            retro_text = build_retro_export(st.session_state.history)
            st.markdown(
                '<div class="colored-block narrative-block">'
                '<div class="block-title narrative-title"><span class="block-title-text"><span class="block-icon-badge"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M17 2l4 4-4 4M3 11V9a3 3 0 0 1 3-3h15M7 22l-4-4 4-4M21 13v2a3 3 0 0 1-3 3H3"/></svg></span>Sprint Retro Export</span></div>',
                unsafe_allow_html=True
            )
            st.code(retro_text, language="text")
            st.download_button("Download sprint retro", data=retro_text,
                              file_name=f"sprint_retro_{date.today().isoformat()}.txt",
                              mime="text/plain", key="dl_retro")

        # ── LLM-BASED RETRO THEMES — alternative/upgrade to the frequency-
        # count export above: one real LLM call over all aggregated history,
        # for genuine recurring-theme analysis instead of exact-text counts. ──
        if st.button("Generate AI retro themes (one AI call)", key="sec_ai_retro_btn"):
            with st.spinner("Analyzing recurring themes across saved standups…"):
                _theme_text, _theme_err = call_llm_retro_themes(st.session_state.history)
            st.markdown(
                '<div class="colored-block narrative-block">'
                '<div class="block-title narrative-title"><span class="block-title-text"><span class="block-icon-badge"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 3l1.8 5.2L19 10l-5.2 1.8L12 17l-1.8-5.2L5 10l5.2-1.8z"/></svg></span>AI Retro Themes</span></div>',
                unsafe_allow_html=True
            )
            if _theme_text:
                st.code(_theme_text, language="text")
                st.download_button("Download AI retro themes", data=_theme_text,
                                  file_name=f"ai_retro_themes_{date.today().isoformat()}.txt",
                                  mime="text/plain", key="dl_ai_retro")
            else:
                st.warning(f"Couldn't generate AI retro themes: {_theme_err}")

# ═══════════════════════════════════════════════════
# SUITE FOOTER — cross-link back to SatiCast. Only shown when the deployer
# has set SATICAST_URL in secrets.
# ═══════════════════════════════════════════════════
_sibling_url = st.secrets.get("SATICAST_URL", "")
if _sibling_url:
    st.markdown(
        f'<div style="text-align:center;margin:3rem 0 1rem;padding-top:1.5rem;'
        f'border-top:1px solid var(--hair);font-size:0.8125rem;color:var(--txt-3);">'
        f'SanghaStatus &nbsp;\u00b7&nbsp; part of the same suite as '
        f'<a href="{_sibling_url}" target="_blank" style="color:var(--accent);font-weight:500;">SatiCast</a>'
        f'</div>',
        unsafe_allow_html=True
    )