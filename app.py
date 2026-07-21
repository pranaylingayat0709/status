import streamlit as st
import json
import re
import hashlib
import urllib.parse
from datetime import date
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
# SESSION STATE
# ═══════════════════════════════════════════════════
def init_state():
    defaults = {
        "history":        [],
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

MAX_HISTORY = 10


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
        blockers = [t for t in tasks if any(
            w in t.lower() for w in ["block", "stuck", "wait", "depend", "issue", "pending"]
        )]
        if header and tasks:
            members.append({"name": header, "tasks": tasks, "blockers": blockers, "count": len(tasks)})
    return members


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
    return (
        f'<div class="loader-wrap">'
        f'<div class="loader-emoji">{emoji}</div>'
        f'<div class="loader-title">{title}</div>'
        f'<div class="loader-sub">{sub} &nbsp;·&nbsp; {stage_idx+1}/{total}</div>'
        f'<div class="loader-dots">{dots}</div>'
        f'<div class="loader-bar-bg"><div class="loader-bar-fg" style="width:{pct}%"></div></div>'
        f'<div class="loader-pct">{pct}%</div>'
        f'</div>'
    )


# ═══════════════════════════════════════════════════
# SYSTEM PROMPT
# ═══════════════════════════════════════════════════
def build_prompt(tone, domain, lang, include_tomorrow, include_blockers):
    tomorrow_key = (
        '"tomorrow_plan": "Good morning, everyone.\\n\\n[Name 1] plans to [tomorrow task].\\n[Name 2] plans to [tomorrow task].\\n\\nThat concludes the plan for tomorrow.",'
        if include_tomorrow else ""
    )
    blocker_key = (
        '"blocker_summary": "Blockers identified today:\\n\\n[Name]: [Blocker detail].\\n(Write \\"No blockers reported today.\\" if none)",'
        if include_blockers else ""
    )
    return f"""
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
- TRANSFORM raw inputs — never copy-paste. Rewrite every phrase into a full professional sentence.
- Each raw task stays as its own separate bullet. Do NOT merge tasks.
- Use hyphen "-" for bullets in chat_update and email_update. Never asterisks.
- Keep each person's updates strictly separated under their name.
- Use correct pronouns inferred from context, or use their name if unclear.
- NO introductory or concluding conversational text in the JSON values.
- Return ONLY a valid JSON object — no markdown fences, no preamble.

Return a JSON object with EXACTLY these keys:
{{
  "standup_narrative": "Good morning, everyone.\\n\\nHere is the status update for [Date].\\n\\n[Name 1]: [narrative].\\n\\n[Name 2]: [narrative].\\n\\nThat concludes today's status update.",
  {tomorrow_key}
  {blocker_key}
  "chat_update": "Daily Project Status Update | [Date]\\n\\n• [Name 1]\\n- [Task 1 sentence].\\n- [Task 2 sentence].\\n\\n• [Name 2]\\n- [Task 1 sentence].",
  "whatsapp_update": "📋 *Daily Status Update | [Date]*\\n\\n*[Name 1]*\\n- [Task 1].\\n\\n*[Name 2]*\\n- [Task 1].",
  "email_update": "Subject: Daily Project Status Update | [Date]\\n\\nDear Team,\\n\\nPlease find below the status update for [Date].\\n\\n[Name 1]\\n- [Task 1].\\n\\n[Name 2]\\n- [Task 1].\\n\\nKindly revert in case of any queries.\\n\\nRegards,\\n[Team Lead Name]"
}}
"""


# ═══════════════════════════════════════════════════
# CSS — pure-CSS dark toggle via :has(), zero Streamlit rerun
# ═══════════════════════════════════════════════════
CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&family=Syne:wght@700;800&display=swap');

:root {
    --app-bg:linear-gradient(-45deg,#ee7752,#e73c7e,#23a6d5,#23d5ab);
    --card-bg:rgba(255,255,255,0.96); --card-bdr:rgba(255,255,255,1);
    --text-h:#0f172a; --text-b:#1e293b; --text-m:#475569;
    --input-bg:#f8fafc; --input-bdr:#cbd5e1; --input-txt:#0f172a;
    /* Inverted colors for dropdown/select widgets — dark box + light text in light theme,
       so we never depend on overriding BaseWeb's own internal text color. */
    --field-bg:#1B1730; --field-txt:#F5F3FF; --field-bdr:rgba(255,255,255,0.2);
    --btn-sh1:rgba(89,15,183,0.4);
    --out-bg:#ffffff; --code-bg:#fafafa; --code-txt:#0f172a;
    --chip-bg:rgba(255,255,255,0.7); --chip-bdr:rgba(0,0,0,0.08);
    --loader-bg:rgba(255,255,255,0.97); --loader-title:#1e1b4b; --loader-sub:#6d28d9;
}
body:has(#dmchk:checked) {
    --app-bg:linear-gradient(-45deg,#0d0221,#0a1628,#12062a,#061220);
    --card-bg:rgba(15,23,42,0.92); --card-bdr:rgba(255,255,255,0.08);
    --text-h:#F1F5F9; --text-b:#CBD5E1; --text-m:#94A3B8;
    --input-bg:rgba(15,23,42,0.95); --input-bdr:rgba(255,0,118,0.35); --input-txt:#F1F5F9;
    /* Inverted colors for dropdown/select widgets — light box + dark text in dark theme. */
    --field-bg:#FFFFFF; --field-txt:#1E1535; --field-bdr:rgba(0,0,0,0.15);
    --btn-sh1:rgba(255,0,118,0.35);
    --out-bg:rgba(15,23,42,0.9); --code-bg:#0f172a; --code-txt:#E2E8F0;
    --chip-bg:rgba(255,255,255,0.06); --chip-bdr:rgba(255,255,255,0.1);
    --loader-bg:rgba(10,15,30,0.96); --loader-title:#DDD6FE; --loader-sub:#A78BFA;
}

html, body, [class*="css"] { font-family:'Inter',sans-serif !important; color:var(--text-b) !important; }
.stApp {
    background:var(--app-bg) !important; background-size:400% 400% !important;
    animation:gradientBG 18s ease infinite !important; min-height:100vh;
}
@keyframes gradientBG { 0%{background-position:0% 50%} 50%{background-position:100% 50%} 100%{background-position:0% 50%} }
.main .block-container { max-width:1240px; padding-top:0.5rem !important; padding-bottom:4rem; padding-left:2rem; padding-right:2rem; }
#MainMenu, footer, header { visibility:hidden; }
* { box-sizing:border-box; }

/* ── PURE-CSS DARK TOGGLE — zero rerun, generation never interrupted ── */
#dmchk { display:none; }
.dm-label {
    position:fixed; top:1.1rem; right:1.4rem; z-index:99999;
    width:58px; height:30px; border-radius:999px; cursor:pointer;
    background:rgba(255,255,255,0.22); border:1.5px solid rgba(255,255,255,0.4);
    display:flex; align-items:center; padding:3px; backdrop-filter:blur(10px);
    box-shadow:0 4px 14px rgba(0,0,0,0.15); transition:all 0.3s ease;
}
.dm-label::after {
    content:'🌙'; width:24px; height:24px; border-radius:50%;
    background:#fff; display:flex; align-items:center; justify-content:center;
    font-size:0.8rem; transition:transform 0.35s cubic-bezier(0.34,1.56,0.64,1);
}
body:has(#dmchk:checked) .dm-label::after { content:'☀️'; transform:translateX(28px); }

/* ── HERO ── */
.hero-section { text-align:center; margin-bottom:2.5rem; position:relative; z-index:1; }
.hero-icon {
    font-size:4.2rem; display:block; margin-bottom:0.7rem;
    animation:floatIcon 3.2s ease-in-out infinite;
    filter:drop-shadow(0 8px 20px rgba(0,0,0,0.2));
}
@keyframes floatIcon { 0%,100%{transform:translateY(0) rotate(-2deg)} 50%{transform:translateY(-10px) rotate(2deg)} }
.main-title {
    font-family:'Syne',sans-serif; font-size:4.4rem; font-weight:900;
    letter-spacing:-2px; margin-bottom:0.4rem;
    background:linear-gradient(120deg,#ffffff,#ffde59,#ffffff,#ffde59);
    background-size:280% auto;
    -webkit-background-clip:text; -webkit-text-fill-color:transparent; background-clip:text;
    text-shadow:0 4px 30px rgba(0,0,0,0.15);
    animation:gradShift 6s linear infinite;
}
@keyframes gradShift { to { background-position:280% center; } }
.main-subtitle {
    color:rgba(255,255,255,0.94) !important; font-size:1.2rem; font-weight:600;
    max-width:680px; margin:0.3rem auto 0; line-height:1.65;
    text-shadow:0 3px 10px rgba(0,0,0,0.12);
}
.sangha-meaning {
    display:inline-flex; align-items:center; gap:8px; margin-top:1rem;
    background:rgba(255,255,255,0.2); border:1.5px solid rgba(255,255,255,0.42);
    border-radius:999px; padding:0.5rem 1.5rem; font-size:0.9rem; font-weight:600;
    color:#ffffff !important; -webkit-text-fill-color:#ffffff !important;
    backdrop-filter:blur(12px); box-shadow:0 6px 20px rgba(0,0,0,0.12);
    animation:fadeUp 0.7s 0.15s ease both;
}
@keyframes fadeUp { from{opacity:0;transform:translateY(12px)} to{opacity:1;transform:translateY(0)} }

/* ── CARDS ── */
.custom-card {
    background:var(--card-bg); border-radius:26px; padding:1.9rem 2.4rem;
    box-shadow:0 18px 46px rgba(0,0,0,0.16); margin-bottom:1.5rem;
    border:1px solid var(--card-bdr); backdrop-filter:blur(20px);
    transition:transform 0.3s ease, box-shadow 0.3s ease;
    animation:cardIn 0.5s ease both;
}
.custom-card:hover { transform:translateY(-3px); box-shadow:0 24px 56px rgba(0,0,0,0.2); }
@keyframes cardIn { from{opacity:0;transform:translateY(20px)} to{opacity:1;transform:translateY(0)} }
.card-header { display:flex; justify-content:space-between; align-items:center; margin-bottom:1.2rem; }
.card-title  { display:flex; align-items:center; gap:16px; }
.icon-circle {
    width:56px; height:56px; border-radius:16px; display:flex; align-items:center; justify-content:center;
    font-size:1.6rem; box-shadow:0 8px 18px rgba(0,0,0,0.14); flex-shrink:0;
    transition:transform 0.3s ease;
}
.custom-card:hover .icon-circle { transform:rotate(-6deg) scale(1.06); }
.blue-icon   { background:linear-gradient(135deg,#3b82f6,#2563eb); }
.green-icon  { background:linear-gradient(135deg,#10b981,#059669); }
.purple-icon { background:linear-gradient(135deg,#8b5cf6,#7c3aed); }
.orange-icon { background:linear-gradient(135deg,#f59e0b,#d97706); }
.title-text { font-size:1.42rem; font-weight:800; color:var(--text-h); }
.desc-text  { color:var(--text-m); font-size:0.92rem; margin-top:0.2rem; }
.side-emoji { font-size:44px; opacity:0.9; }

/* ── INPUTS ── */
.stTextArea textarea, .stTextInput input {
    background-color:var(--input-bg) !important; border:2px solid var(--input-bdr) !important;
    border-radius:16px !important; color:var(--input-txt) !important;
    font-size:1rem !important; font-weight:500 !important; transition:all 0.25s ease !important;
}
.stTextArea textarea { min-height:230px !important; line-height:1.8 !important; padding:1rem !important; }
.stTextArea textarea:focus, .stTextInput input:focus {
    border-color:#FF0076 !important; box-shadow:0 0 0 4px rgba(255,0,118,0.15) !important;
}
div[data-testid="stSelectbox"] > div > div, div[data-testid="stDateInput"] > div > div {
    background:var(--field-bg) !important; border:2px solid var(--field-bdr) !important;
    border-radius:16px !important; color:var(--field-txt) !important;
}
/* Selected value text inside the closed selectbox/date-input — using INVERTED colors
   (dark box + light text in light theme, light box + dark text in dark theme) so
   contrast is guaranteed regardless of how BaseWeb renders its internal spans. */
div[data-testid="stSelectbox"] div[data-baseweb="select"] *,
div[data-testid="stDateInput"] input {
    color:var(--field-txt) !important;
    -webkit-text-fill-color:var(--field-txt) !important;
}
div[data-testid="stSelectbox"] div[aria-disabled="true"] * {
    color:var(--field-txt) !important;
    opacity:0.85 !important;
    -webkit-text-fill-color:var(--field-txt) !important;
}
/* The dropdown OPTIONS LIST is rendered in a portal appended to <body>, so it must be
   themed globally — also using inverted field colors. */
div[data-baseweb="popover"] ul,
div[data-baseweb="menu"] {
    background:var(--field-bg) !important;
    border:1.5px solid var(--field-bdr) !important;
    border-radius:12px !important;
}
div[data-baseweb="popover"] li,
div[data-baseweb="menu"] li,
div[data-baseweb="popover"] [role="option"],
div[data-baseweb="menu"] [role="option"] {
    color:var(--field-txt) !important;
    -webkit-text-fill-color:var(--field-txt) !important;
    background:transparent !important;
}
div[data-baseweb="popover"] li:hover,
div[data-baseweb="menu"] li:hover,
div[data-baseweb="popover"] [role="option"]:hover,
div[data-baseweb="menu"] [role="option"]:hover {
    background:rgba(128,128,128,0.2) !important;
}
div[data-testid="stSelectbox"] label, div[data-testid="stTextInput"] label,
div[data-testid="stDateInput"] label, div[data-testid="stTextArea"] label {
    color:var(--text-h) !important; font-weight:700 !important; font-size:0.8rem !important;
    letter-spacing:0.06em !important; text-transform:uppercase !important;
}
.stCheckbox label p { color:var(--text-h) !important; font-weight:600 !important; }

/* ── MEMBER CHIPS ── */
.member-chips { display:flex; flex-wrap:wrap; gap:12px; margin-top:1.1rem; }
.member-chip {
    background:var(--chip-bg); border:1.5px solid var(--chip-bdr); border-radius:14px;
    padding:0.7rem 1.1rem; backdrop-filter:blur(8px);
    transition:transform 0.2s ease, box-shadow 0.2s ease;
    animation:chipIn 0.4s ease both;
}
.member-chip:hover { transform:translateY(-3px); box-shadow:0 10px 24px rgba(0,0,0,0.12); }
@keyframes chipIn { from{opacity:0;transform:scale(0.9)} to{opacity:1;transform:scale(1)} }
.chip-name  { font-weight:800; font-size:0.94rem; color:var(--text-h); }
.chip-tasks { font-size:0.76rem; color:var(--text-m); margin-top:0.15rem; }
.chip-block { font-size:0.72rem; color:#ef4444; font-weight:700; margin-top:0.2rem; }

/* ── MAIN BUTTON ── */
.stButton > button {
    background:linear-gradient(135deg,#FF0076 0%,#590FB7 100%) !important;
    color:#fff !important; border:none !important; border-radius:50px !important;
    padding:1.05rem 4.2rem !important; font-size:1.15rem !important; font-weight:800 !important;
    letter-spacing:0.05em; display:block; margin:2rem auto;
    box-shadow:0 10px 30px var(--btn-sh1) !important;
    transition:all 0.3s cubic-bezier(0.4,0,0.2,1) !important;
}
.stButton > button:hover { transform:translateY(-4px) scale(1.02) !important; box-shadow:0 18px 42px rgba(255,0,118,0.5) !important; }
.stButton > button:active { transform:scale(0.97) !important; }

/* ── LOADER ── */
@keyframes loaderFadeIn { from{opacity:0;transform:translateY(24px)} to{opacity:1;transform:translateY(0)} }
@keyframes loaderBounce { 0%,100%{transform:translateY(0) scale(1)} 40%{transform:translateY(-14px) scale(1.14)} 65%{transform:translateY(-6px) scale(1.06)} }
@keyframes shimmer { 0%{background-position:200% 0} 100%{background-position:-200% 0} }
@keyframes dotPop { from{transform:scale(0.3);opacity:0} to{transform:scale(1);opacity:1} }
.loader-wrap {
    background:var(--loader-bg); border-radius:28px; padding:3rem 2.5rem; text-align:center;
    max-width:580px; margin:1.5rem auto; box-shadow:0 28px 70px rgba(0,0,0,0.25);
    animation:loaderFadeIn 0.4s cubic-bezier(0.34,1.56,0.64,1) both;
    border:1.5px solid rgba(255,255,255,0.12);
}
.loader-emoji { font-size:3.4rem; display:block; margin-bottom:0.9rem; animation:loaderBounce 1.4s ease-in-out infinite; }
.loader-title { font-family:'Syne',sans-serif; font-size:1.35rem; font-weight:800; margin-bottom:0.35rem; color:var(--loader-title); }
.loader-sub   { font-size:0.84rem; font-weight:600; margin-bottom:1.6rem; color:var(--loader-sub); }
.loader-dots  { display:flex; justify-content:center; gap:9px; margin-bottom:1.5rem; }
.ld { width:11px; height:11px; border-radius:50%; background:#e5e7eb; transition:background 0.3s; }
.lactive { background:linear-gradient(135deg,#FF0076,#590FB7); animation:dotPop 0.4s cubic-bezier(0.34,1.56,0.64,1) both; box-shadow:0 0 10px rgba(255,0,118,0.5); }
.ldone { background:#590FB7; }
.loader-bar-bg { height:7px; border-radius:99px; background:rgba(89,15,183,0.1); overflow:hidden; margin-bottom:0.6rem; }
.loader-bar-fg {
    height:100%; border-radius:99px; background:linear-gradient(90deg,#FF0076,#590FB7,#23a6d5,#FF0076);
    background-size:200% 100%; animation:shimmer 1.5s linear infinite;
    transition:width 0.4s cubic-bezier(0.4,0,0.2,1);
}
.loader-pct { font-size:0.8rem; font-weight:800; letter-spacing:0.06em; color:var(--loader-sub); }

/* ── OUTPUT GRID: 2 columns wide-screen ── */
.output-grid { display:grid; grid-template-columns:1fr 1fr; gap:1.5rem; }
@media (max-width:900px) { .output-grid { grid-template-columns:1fr; } }

@keyframes blockReveal { from{opacity:0;transform:translateY(22px)} to{opacity:1;transform:translateY(0)} }
.colored-block {
    padding:1.75rem 2rem; border-radius:22px;
    background:var(--out-bg); box-shadow:0 10px 32px rgba(0,0,0,0.09);
    animation:blockReveal 0.5s ease both;
    transition:transform 0.25s ease, box-shadow 0.25s ease;
}
.colored-block:hover { transform:translateY(-4px); box-shadow:0 18px 40px rgba(0,0,0,0.14); }
.narrative-block { border-left:7px solid #4f46e5; background:rgba(79,70,229,0.045); animation-delay:0.05s; grid-column:1/-1; }
.chat-block      { border-left:7px solid #ec4899; background:rgba(236,72,153,0.045); animation-delay:0.12s; }
.whatsapp-block  { border-left:7px solid #25D366; background:rgba(37,211,102,0.045); animation-delay:0.19s; }
.email-block     { border-left:7px solid #f59e0b; background:rgba(245,158,11,0.045); animation-delay:0.26s; grid-column:1/-1; }
.tomorrow-block  { border-left:7px solid #06b6d4; background:rgba(6,182,212,0.045);  animation-delay:0.33s; }
.blocker-block   { border-left:7px solid #ef4444; background:rgba(239,68,68,0.045);  animation-delay:0.40s; }

.block-title {
    font-size:1.28rem; font-weight:900; margin-bottom:1rem;
    display:flex; align-items:center; justify-content:space-between; gap:12px;
}
.narrative-title { color:#4f46e5; } .chat-title { color:#db2777; }
.whatsapp-title  { color:#128C7E; } .email-title { color:#d97706; }
.tomorrow-title  { color:#0891b2; } .blocker-title { color:#dc2626; }

.action-btn {
    display:inline-flex; align-items:center; gap:6px;
    background:rgba(0,0,0,0.06); border:1.5px solid rgba(0,0,0,0.1); border-radius:999px;
    padding:0.4rem 1.1rem; font-size:0.8rem; font-weight:700;
    color:var(--text-h); text-decoration:none; transition:all 0.2s;
}
.action-btn:hover { background:rgba(255,0,118,0.1); border-color:rgba(255,0,118,0.3); transform:translateY(-1px); }

/* ── CODE BLOCKS ── */
pre {
    border-radius:16px !important; background:var(--code-bg) !important;
    border:1.5px solid rgba(0,0,0,0.06) !important; padding:1.25rem !important;
    color:var(--code-txt) !important; font-size:0.94rem !important; line-height:1.75 !important;
}

/* ── STATS ROW ── */
.stats-row { display:grid; grid-template-columns:repeat(3,1fr); gap:14px; margin:1.6rem 0 0; }
@media (max-width:600px) { .stats-row { grid-template-columns:1fr; } }
.stat-chip {
    background:var(--chip-bg); border:1.5px solid var(--chip-bdr); border-radius:16px;
    padding:0.9rem 1.2rem; backdrop-filter:blur(8px); text-align:center;
    transition:transform 0.2s ease;
}
.stat-chip:hover { transform:translateY(-3px); }
.stat-val { font-family:'Syne',sans-serif; font-size:1.7rem; font-weight:800; color:var(--text-h); }
.stat-lbl { font-size:0.74rem; font-weight:700; letter-spacing:0.08em; text-transform:uppercase; color:var(--text-m); margin-top:0.15rem; }

/* ── TOKEN BADGE ── */
.token-row { text-align:center; margin:1.8rem 0 0; }
.token-badge {
    display:inline-block; background:rgba(255,255,255,0.18); border:1.5px solid rgba(255,255,255,0.35);
    border-radius:999px; padding:0.5rem 1.5rem; color:#fff !important; font-weight:700; font-size:0.86rem;
    backdrop-filter:blur(10px);
}

/* ── HISTORY ── */
.hist-card {
    background:var(--card-bg); border:1.5px solid var(--card-bdr); border-radius:18px;
    padding:1.1rem 1.4rem; margin-bottom:0.85rem; backdrop-filter:blur(12px);
    display:flex; justify-content:space-between; align-items:flex-start; gap:12px;
    transition:transform 0.2s ease;
}
.hist-card:hover { transform:translateY(-2px); }
.hist-date { font-family:'Syne',sans-serif; font-size:0.95rem; font-weight:800; color:var(--text-h); }
.hist-meta { font-size:0.76rem; color:var(--text-m); margin-top:0.2rem; }

details { background:var(--card-bg) !important; border-radius:18px !important; border:1.5px solid var(--card-bdr) !important; padding:0.5rem 1rem !important; margin-bottom:1rem !important; }
details summary { color:var(--text-h) !important; font-weight:700 !important; cursor:pointer; }

@media (max-width:768px) {
    .main-title  { font-size:2.8rem; }
    .title-text  { font-size:1.2rem; }
    .side-emoji  { display:none; }
    .card-header { flex-direction:column; align-items:flex-start; gap:12px; }
    .loader-wrap { padding:2rem 1.25rem; }
}
</style>
"""

st.markdown(CSS, unsafe_allow_html=True)
st.markdown('<input type="checkbox" id="dmchk"><label for="dmchk" class="dm-label"></label>', unsafe_allow_html=True)

# ═══════════════════════════════════════════════════
# HERO
# ═══════════════════════════════════════════════════
st.markdown(
    '<div class="hero-section">'
    '<span class="hero-icon">🏛️</span>'
    '<div class="main-title">Sangha<span></span>Status</div>'
    '<div class="main-subtitle">Professional standup narratives, chat updates, WhatsApp messages &amp; emails — generated in seconds.</div>'
    '<div class="sangha-meaning">✦ Sangha — the Pali word for "community" or "assembly" &nbsp;·&nbsp; Focusing on the Team ✦</div>'
    '</div>',
    unsafe_allow_html=True
)

# ═══════════════════════════════════════════════════
# CONFIGURATION CARD
# ═══════════════════════════════════════════════════
st.markdown(
    '<div class="custom-card">'
    '<div class="card-header"><div class="card-title">'
    '<div class="icon-circle purple-icon">⚙️</div>'
    '<div><div class="title-text">Configuration</div>'
    '<div class="desc-text">Set the date, tone, domain, and output language for this standup.</div></div>'
    '</div><div class="side-emoji">🎛️</div></div>',
    unsafe_allow_html=True
)

cfg1, cfg2, cfg3, cfg4 = st.columns(4)
with cfg1:
    standup_date = st.date_input("📅 Standup Date", value=date.today(), key="pref_date")
with cfg2:
    tone_choice = st.selectbox("🎨 Tone", options=list(TONE_OPTIONS.keys()), index=1, key="pref_tone")
with cfg3:
    domain_choice = st.selectbox("🏢 Domain", options=list(DOMAIN_OPTIONS.keys()), index=0, key="pref_domain")
with cfg4:
    lang_choice = st.selectbox("🌐 Output Language", options=list(OUTPUT_LANG_OPTIONS.keys()), index=0, key="pref_lang")

cfg5, cfg6, cfg7 = st.columns(3)
with cfg5:
    project_name = st.text_input("📁 Project / Sprint Tag", placeholder="e.g. Phoenix · Sprint 14", key="pref_project")
with cfg6:
    include_tomorrow = st.checkbox("📅 Include Tomorrow's Plan", value=False, key="pref_tomorrow")
with cfg7:
    include_blockers = st.checkbox("🚧 Highlight Blockers", value=True, key="pref_blockers")

st.markdown("</div>", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════
# RAW UPDATES CARD
# ═══════════════════════════════════════════════════
st.markdown(
    '<div class="custom-card">'
    '<div class="card-header"><div class="card-title">'
    '<div class="icon-circle green-icon">📝</div>'
    '<div><div class="title-text">Raw Updates</div>'
    '<div class="desc-text">Paste your team\'s raw notes below — works for engineering, functional, or HR teams. Names are auto-detected.</div></div>'
    '</div><div class="side-emoji">📋</div></div>',
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
    key="raw_input"
)

members = parse_members(raw_updates) if raw_updates.strip() else []

if members:
    total_tasks    = sum(m["count"] for m in members)
    total_blockers = sum(len(m["blockers"]) for m in members)
    st.markdown(
        f'<div class="stats-row">'
        f'<div class="stat-chip"><div class="stat-val">{len(members)}</div><div class="stat-lbl">Members</div></div>'
        f'<div class="stat-chip"><div class="stat-val">{total_tasks}</div><div class="stat-lbl">Total Tasks</div></div>'
        f'<div class="stat-chip"><div class="stat-val">{total_blockers}</div><div class="stat-lbl">Blockers</div></div>'
        f'</div>',
        unsafe_allow_html=True
    )
    chips = ""
    for m in members:
        bl = (f'<div class="chip-block">⚠️ {len(m["blockers"])} blocker{"s" if len(m["blockers"])>1 else ""}</div>'
              if m["blockers"] else "")
        chips += (
            f'<div class="member-chip"><div class="chip-name">{m["name"]}</div>'
            f'<div class="chip-tasks">{m["count"]} task{"s" if m["count"]!=1 else ""}</div>{bl}</div>'
        )
    st.markdown(f'<div class="member-chips">{chips}</div>', unsafe_allow_html=True)

st.markdown("</div>", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════
# GENERATE
# ═══════════════════════════════════════════════════
generate = st.button("✨ Generate Professional Status")

if generate:
    if not raw_updates.strip():
        st.warning("⚠️ Please paste your team's raw updates first.")
    elif not members:
        st.warning("⚠️ Could not detect any team member names. Use 'Name:' format.")
    else:
        slot = st.empty()
        slot.markdown(render_loader(0), unsafe_allow_html=True)

        try:
            fmt_date    = standup_date.strftime("%B %d, %Y")
            project_tag = f" | {project_name}" if project_name.strip() else ""
            tone_instr  = TONE_OPTIONS[tone_choice]
            domain_str  = DOMAIN_OPTIONS[domain_choice]
            lang_str    = OUTPUT_LANG_OPTIONS[lang_choice]

            prompt_payload = f"""
Use this date for all sections: {fmt_date}
Project/Sprint: {project_name or "General"}
Team Members detected: {len(members)} ({', '.join(m['name'] for m in members)})

Raw Updates:
{raw_updates}

Embed the project tag "{project_tag}" in the chat_update header and email subject line.
"""
            system_prompt = build_prompt(tone_instr, domain_str, lang_str, include_tomorrow, include_blockers)

            slot.markdown(render_loader(1), unsafe_allow_html=True)

            completion = client.chat.completions.create(
                model="nvidia/llama-3.3-nemotron-super-49b-v1",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user",   "content": prompt_payload}
                ],
                temperature=0.1,
                max_tokens=2000,
                response_format={"type": "json_object"}
            )

            data = json.loads(completion.choices[0].message.content)

            slot.markdown(render_loader(2), unsafe_allow_html=True)

            if hasattr(completion, "usage") and completion.usage:
                st.session_state.session_tokens += completion.usage.total_tokens

            st.session_state.history.insert(0, {
                "date": fmt_date, "project": project_name or "—",
                "members": len(members), "tasks": sum(m["count"] for m in members),
                "tone": tone_choice, "domain": domain_choice, "lang": lang_choice,
                "data": data,
            })
            st.session_state.history = st.session_state.history[:MAX_HISTORY]

            slot.empty()
            st.markdown("<br>", unsafe_allow_html=True)

            narrative = data.get("standup_narrative", "")
            chat      = data.get("chat_update", "")
            wa        = data.get("whatsapp_update", "")
            email_raw = data.get("email_update", "")

            lines      = email_raw.splitlines()
            subj_line  = next((l for l in lines if l.lower().startswith("subject:")), "")
            subj       = subj_line.replace("Subject:", "").replace("subject:", "").strip()
            body_lines = [l for l in lines if l != subj_line]
            body_text  = "\n".join(body_lines).strip()
            mailto     = mailto_link(subj, body_text)

            st.markdown('<div class="output-grid">', unsafe_allow_html=True)

            # Narrative — full width
            st.markdown(
                '<div class="colored-block narrative-block">'
                '<div class="block-title narrative-title"><span>🗣️ Standup Narrative</span></div>',
                unsafe_allow_html=True
            )
            st.code(narrative, language="text")
            st.markdown("</div>", unsafe_allow_html=True)

            # Chat + WhatsApp side by side
            st.markdown(
                '<div class="colored-block chat-block">'
                '<div class="block-title chat-title"><span>💬 Chat Update (Slack / Teams)</span></div>',
                unsafe_allow_html=True
            )
            st.code(chat, language="text")
            st.markdown("</div>", unsafe_allow_html=True)

            st.markdown(
                '<div class="colored-block whatsapp-block">'
                '<div class="block-title whatsapp-title"><span>📱 WhatsApp Update</span></div>',
                unsafe_allow_html=True
            )
            st.code(wa, language="text")
            st.markdown("</div>", unsafe_allow_html=True)

            # Email — full width with mailto button
            st.markdown(
                f'<div class="colored-block email-block">'
                f'<div class="block-title email-title">'
                f'<span>📧 Email Update</span>'
                f'<a class="action-btn" href="{mailto}">✉️ Open in Mail App</a></div>',
                unsafe_allow_html=True
            )
            st.code(email_raw, language="text")
            st.markdown("</div>", unsafe_allow_html=True)

            if include_tomorrow and data.get("tomorrow_plan"):
                st.markdown(
                    '<div class="colored-block tomorrow-block">'
                    '<div class="block-title tomorrow-title">📅 Tomorrow\'s Plan</div>',
                    unsafe_allow_html=True
                )
                st.code(data["tomorrow_plan"], language="text")
                st.markdown("</div>", unsafe_allow_html=True)

            if include_blockers and data.get("blocker_summary"):
                st.markdown(
                    '<div class="colored-block blocker-block">'
                    '<div class="block-title blocker-title">🚧 Blockers Summary</div>',
                    unsafe_allow_html=True
                )
                st.code(data["blocker_summary"], language="text")
                st.markdown("</div>", unsafe_allow_html=True)

            st.markdown("</div>", unsafe_allow_html=True)  # close output-grid

            run_tokens = completion.usage.total_tokens if hasattr(completion, "usage") and completion.usage else 0
            st.markdown(
                f'<div class="token-row"><div class="token-badge">'
                f'🛡️ This run: {run_tokens:,} tokens &nbsp;·&nbsp; '
                f'Session total: {st.session_state.session_tokens:,} tokens &nbsp;·&nbsp; '
                f'Runs saved: {len(st.session_state.history)}</div></div>',
                unsafe_allow_html=True
            )

        except json.JSONDecodeError:
            slot.empty()
            st.warning("⚠️ Malformed response — retrying once…")
            try:
                completion2 = client.chat.completions.create(
                    model="nvidia/llama-3.3-nemotron-super-49b-v1",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user",   "content": prompt_payload}
                    ],
                    temperature=0.05,
                    max_tokens=2000,
                    response_format={"type": "json_object"}
                )
                data2 = json.loads(completion2.choices[0].message.content)
                st.success("✅ Retry succeeded!")
                st.code(data2.get("standup_narrative", ""), language="text")
            except Exception:
                st.error("❌ Both attempts failed. Please try again.")
        except Exception as e:
            slot.empty()
            st.error(f"❌ Error: {e}")

# ═══════════════════════════════════════════════════
# HISTORY
# ═══════════════════════════════════════════════════
if st.session_state.history:
    st.markdown("<br>", unsafe_allow_html=True)
    with st.expander(f"🕘 Past Standups ({len(st.session_state.history)} saved) — click to expand & replay", expanded=False):
        for idx, entry in enumerate(st.session_state.history):
            st.markdown(
                f'<div class="hist-card"><div>'
                f'<div class="hist-date">📅 {entry["date"]} &nbsp;·&nbsp; {entry.get("project","—")}</div>'
                f'<div class="hist-meta">👥 {entry["members"]} members &nbsp;·&nbsp; ✅ {entry["tasks"]} tasks '
                f'&nbsp;·&nbsp; {entry["tone"]} &nbsp;·&nbsp; {entry["domain"]} &nbsp;·&nbsp; {entry["lang"]}</div>'
                f'</div></div>',
                unsafe_allow_html=True
            )
            with st.expander(f"View outputs — {entry['date']}", expanded=False):
                d = entry["data"]
                st.markdown("**🗣️ Narrative**")
                st.code(d.get("standup_narrative", ""), language="text")
                st.markdown("**💬 Chat**")
                st.code(d.get("chat_update", ""), language="text")
                st.markdown("**📱 WhatsApp**")
                st.code(d.get("whatsapp_update", ""), language="text")
                st.markdown("**📧 Email**")
                st.code(d.get("email_update", ""), language="text")
                if d.get("tomorrow_plan"):
                    st.markdown("**📅 Tomorrow**")
                    st.code(d["tomorrow_plan"], language="text")
                if d.get("blocker_summary"):
                    st.markdown("**🚧 Blockers**")
                    st.code(d["blocker_summary"], language="text")

        if st.button("🗑️ Clear all history", key="clear_hist"):
            st.session_state.history = []
            st.rerun()