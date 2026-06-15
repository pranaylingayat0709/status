import streamlit as st
import json
from openai import OpenAI
from datetime import datetime
import time

# ---------------------------------------------------
# PAGE CONFIG
# ---------------------------------------------------
st.set_page_config(
    page_title="SanghaStatus",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ---------------------------------------------------
# API KEY CHECK
# ---------------------------------------------------
if "NVIDIA_API_KEY" not in st.secrets:
    st.error("🔑 NVIDIA_API_KEY not found in Streamlit secrets.")
    st.stop()

# ---------------------------------------------------
# CLIENT
# ---------------------------------------------------
client = OpenAI(
    base_url="https://integrate.api.nvidia.com/v1",
    api_key=st.secrets["NVIDIA_API_KEY"]
)

# ---------------------------------------------------
# SYSTEM PROMPT
# ---------------------------------------------------
SYSTEM_INSTRUCTIONS = """
You are SanghaStatus, a precise professional assistant.

STRICT RULES FOR FORMATTING & WRITING (CRITICAL):
- TRANSFORM RAW INPUTS: DO NOT just copy-paste the raw bullet points. You MUST rewrite and expand every single short phrase into a full, professional, action-oriented sentence ending with a period.
  * Bad: "- working on masking"
  * Good: "- Currently working on implementing masking enhancements."
- DO NOT combine, merge, or summarize sentences. Each raw task must remain its own standalone bullet point.
- ALWAYS use a standard hyphen "-" for bullet points in the Chat and Email updates. Do not use asterisks.
- Keep each person's updates strictly separated under their name.
- DO NOT add any introductory or concluding conversational text.
- You MUST output a valid JSON object with EXACTLY three keys: "standup_narrative", "chat_update", and "email_update".

EXPECTED JSON STRUCTURE AND TEMPLATE:

{
  "standup_narrative": "Good morning, everyone.\\n\\nHere is the status update for [Insert Provided Date].\\n\\nStarting with [Name 1], he/she is currently focused on [Rewrite task into narrative].\\n\\nMoving on to [Name 2], he/she is progressing with [Rewrite task into narrative].\\n\\nFinally, [Name 3] is concentrating on [Rewrite task into narrative].\\n\\nThat concludes today's status update.",

  "chat_update": "Daily Project Status Update | [Insert Provided Date]\\n\\n• [Name 1]\\n- [Expanded, complete professional sentence for Task 1].\\n- [Expanded, complete professional sentence for Task 2].\\n\\n• [Name 2]\\n- [Expanded, complete professional sentence for Task 1].",

  "email_update": "Subject: Daily Project Status Update | [Insert Provided Date]\\n\\nDear Team,\\n\\nI am writing to share the status for the activities performed on [Insert Provided Date].\\n\\n[Name 1]\\n- [Expanded, complete professional sentence for Task 1].\\n- [Expanded, complete professional sentence for Task 2].\\n\\n[Name 2]\\n- [Expanded, complete professional sentence for Task 1].\\n\\nLet me know in case you need more details.\\n\\nRegards,\\n[Name]"
}
"""

# ---------------------------------------------------
# LOADER STAGES
# ---------------------------------------------------
LOADER_STAGES = [
    ("🏛️", "Gathering the Sangha…",              "Assembling your team's raw updates"),
    ("📖", "Reading every task carefully…",       "Parsing each team member's input"),
    ("✍️", "Rewriting into professional prose…",  "Expanding short notes into full sentences"),
    ("🗣️", "Crafting the standup narrative…",     "Building the spoken script"),
    ("💬", "Composing the chat update…",          "Formatting for team channels"),
    ("📧", "Drafting the email…",                 "Polishing subject line and body"),
    ("✨", "Finalising your update…",             "Running final quality check"),
]

def render_loader(stage_idx: int) -> str:
    total = len(LOADER_STAGES)
    emoji, title, sub = LOADER_STAGES[stage_idx]
    pct = int((stage_idx + 1) / total * 100)
    dots = "".join([
        f'<div class="ld {"ldone" if i < stage_idx else ("lactive" if i == stage_idx else "")}"></div>'
        for i in range(total)
    ])
    return f"""
    <div class="loader-wrap">
        <div class="loader-emoji">{emoji}</div>
        <div class="loader-title">{title}</div>
        <div class="loader-sub">{sub} &nbsp;·&nbsp; Step {stage_idx + 1} of {total}</div>
        <div class="loader-dots">{dots}</div>
        <div class="loader-bar-bg">
            <div class="loader-bar-fg" style="width:{pct}%"></div>
        </div>
        <div class="loader-pct">{pct}%</div>
    </div>
    """

# ---------------------------------------------------
# CUSTOM CSS
# ---------------------------------------------------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800;900&family=Syne:wght@700;800&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

/* ── ANIMATED GRADIENT BG ── */
@keyframes gradientBG {
    0%   { background-position: 0% 50%; }
    50%  { background-position: 100% 50%; }
    100% { background-position: 0% 50%; }
}
.stApp {
    background: linear-gradient(-45deg, #ee7752, #e73c7e, #23a6d5, #23d5ab);
    background-size: 400% 400%;
    animation: gradientBG 15s ease infinite;
    min-height: 100vh;
}
.main .block-container {
    max-width: 1000px;
    padding-top: 2rem;
    padding-bottom: 4rem;
}
#MainMenu, footer, header { visibility: hidden; }

/* ── HERO ── */
.hero-section { text-align: center; margin-bottom: 3.5rem; }

.hero-icon {
    font-size: 4rem; display: block; margin-bottom: 0.75rem;
    animation: floatIcon 3s ease-in-out infinite;
}
@keyframes floatIcon {
    0%,100% { transform: translateY(0); }
    50%     { transform: translateY(-9px); }
}

.main-title {
    font-family: 'Syne', sans-serif;
    font-size: 4rem; font-weight: 900;
    color: #ffffff !important;
    letter-spacing: -1.5px; margin-bottom: 0.4rem;
    text-shadow: 0 10px 20px rgba(0,0,0,0.18);
}
.main-title span { color: #ffde59 !important; }

.main-subtitle {
    color: rgba(255,255,255,0.95) !important;
    font-size: 1.2rem; font-weight: 600;
    max-width: 650px; margin: 0.3rem auto 0;
    line-height: 1.6; text-shadow: 0 4px 10px rgba(0,0,0,0.1);
}

/* Meaning pill */
.sangha-meaning {
    display: inline-block; margin-top: 0.85rem;
    background: rgba(255,255,255,0.18);
    border: 1.5px solid rgba(255,255,255,0.4);
    border-radius: 999px; padding: 0.4rem 1.4rem;
    font-size: 0.88rem; font-weight: 600;
    color: #ffffff !important;
    letter-spacing: 0.02em; backdrop-filter: blur(10px);
    text-shadow: 0 2px 6px rgba(0,0,0,0.12);
}

/* ── CARDS ── */
.custom-card {
    background: rgba(255,255,255,0.96);
    border-radius: 28px; padding: 2.5rem;
    box-shadow: 0 20px 50px rgba(0,0,0,0.2);
    margin-bottom: 2rem;
    border: 1px solid rgba(255,255,255,1);
    backdrop-filter: blur(20px);
}
.card-header { display:flex; justify-content:space-between; align-items:center; margin-bottom:1.5rem; }
.card-title  { display:flex; align-items:center; gap:20px; }
.icon-circle {
    width:65px; height:65px; border-radius:20px;
    display:flex; align-items:center; justify-content:center;
    font-size:1.8rem; box-shadow:0 8px 15px rgba(0,0,0,0.08);
}
.blue-icon  { background:#3b82f6; color:#fff; }
.green-icon { background:#10b981; color:#fff; }
.title-text { font-size:1.6rem; font-weight:800; color:#0f172a; }
.desc-text  { color:#475569; font-size:1rem; margin-top:0.3rem; }
.side-emoji { font-size:50px; }

/* ── INPUTS ── */
.stNumberInput input, .stTextArea textarea {
    background-color: #f8fafc !important;
    border: 2px solid #cbd5e1 !important;
    border-radius: 18px !important;
    color: #0f172a !important;
    padding: 1.2rem !important;
    font-size: 1.05rem !important;
    font-weight: 600 !important;
    transition: all 0.3s ease !important;
}
.stTextArea textarea { min-height: 250px !important; line-height: 1.8 !important; }
.stNumberInput input:focus, .stTextArea textarea:focus {
    border-color: #e73c7e !important;
    box-shadow: 0 0 0 4px rgba(231,60,126,0.2) !important;
}

/* ── BUTTON ── */
.stButton > button {
    background: linear-gradient(135deg, #FF0076 0%, #590FB7 100%) !important;
    color: #fff !important; border: none !important;
    border-radius: 50px !important; padding: 1.2rem 4rem !important;
    font-size: 1.2rem !important; font-weight: 800 !important;
    letter-spacing: 1px; display: block; margin: 2.5rem auto;
    box-shadow: 0 10px 25px rgba(89,15,183,0.4) !important;
    transition: all 0.3s cubic-bezier(0.4,0,0.2,1) !important;
}
.stButton > button:hover {
    transform: translateY(-5px) scale(1.02);
    box-shadow: 0 15px 35px rgba(255,0,118,0.5) !important;
}

/* ── ANIMATED LOADER CARD ── */
@keyframes loaderFadeIn {
    from { opacity:0; transform:translateY(24px); }
    to   { opacity:1; transform:translateY(0); }
}
@keyframes loaderBounce {
    0%,100% { transform: translateY(0) scale(1); }
    40%     { transform: translateY(-14px) scale(1.14); }
    65%     { transform: translateY(-6px)  scale(1.06); }
}
@keyframes shimmer {
    0%   { background-position: 200% 0; }
    100% { background-position: -200% 0; }
}
@keyframes dotPop {
    from { transform: scale(0.3); opacity:0; }
    to   { transform: scale(1);   opacity:1; }
}

.loader-wrap {
    background: rgba(255,255,255,0.97);
    border-radius: 28px; padding: 3rem 2.5rem;
    text-align: center; max-width: 580px; margin: 2rem auto;
    box-shadow: 0 28px 70px rgba(0,0,0,0.25);
    animation: loaderFadeIn 0.4s cubic-bezier(0.34,1.56,0.64,1) both;
    border: 1.5px solid rgba(255,255,255,0.9);
}
.loader-emoji {
    font-size: 3.4rem; display: block; margin-bottom: 0.9rem;
    animation: loaderBounce 1.4s ease-in-out infinite;
}
.loader-title {
    font-family: 'Syne', sans-serif;
    font-size: 1.35rem; font-weight: 800;
    color: #1e1b4b; margin-bottom: 0.35rem;
}
.loader-sub {
    font-size: 0.84rem; color: #6d28d9;
    font-weight: 600; margin-bottom: 1.6rem;
}
.loader-dots {
    display: flex; justify-content: center;
    gap: 9px; margin-bottom: 1.5rem;
}
.ld {
    width: 11px; height: 11px; border-radius: 50%;
    background: #e5e7eb;
    transition: background 0.3s ease;
}
.lactive {
    background: linear-gradient(135deg, #FF0076, #590FB7);
    animation: dotPop 0.4s cubic-bezier(0.34,1.56,0.64,1) both;
    box-shadow: 0 0 8px rgba(255,0,118,0.4);
}
.ldone { background: #590FB7; }

.loader-bar-bg {
    height: 7px; border-radius: 99px;
    background: rgba(89,15,183,0.1);
    overflow: hidden; margin-bottom: 0.6rem;
}
.loader-bar-fg {
    height: 100%; border-radius: 99px;
    background: linear-gradient(90deg, #FF0076, #590FB7, #23a6d5, #FF0076);
    background-size: 200% 100%;
    animation: shimmer 1.6s linear infinite;
    transition: width 0.6s cubic-bezier(0.4,0,0.2,1);
}
.loader-pct {
    font-size: 0.8rem; font-weight: 800;
    color: #590FB7; letter-spacing: 0.06em;
}

/* ── OUTPUT BLOCKS ── */
@keyframes blockReveal {
    from { opacity:0; transform: translateY(18px); }
    to   { opacity:1; transform: translateY(0); }
}
.colored-block {
    padding: 2rem; border-radius: 24px; margin-bottom: 2rem;
    background: #ffffff; box-shadow: 0 10px 30px rgba(0,0,0,0.06);
    position: relative; overflow: hidden;
    animation: blockReveal 0.5s ease both;
}
.narrative-block { border-left: 8px solid #4f46e5; background: rgba(79,70,229,0.03); animation-delay: 0.05s; }
.chat-block      { border-left: 8px solid #ec4899; background: rgba(236,72,153,0.03); animation-delay: 0.15s; }
.email-block     { border-left: 8px solid #f59e0b; background: rgba(245,158,11,0.03); animation-delay: 0.25s; }

.block-title {
    font-size: 1.4rem; font-weight: 900; margin-bottom: 1.2rem;
    display: flex; align-items: center; gap: 12px;
}
.narrative-title { color: #4f46e5; }
.chat-title      { color: #db2777; }
.email-title     { color: #d97706; }

/* ── CODE BLOCKS ── */
pre {
    border-radius: 16px !important; background: #fafafa !important;
    border: 2px solid rgba(0,0,0,0.05) !important; padding: 1.5rem !important;
    color: #0f172a !important; font-size: 1rem !important;
    box-shadow: inset 0 4px 10px rgba(0,0,0,0.02) !important;
}

/* ── TOKEN BADGE ── */
.token-badge {
    text-align: center; margin: 1rem auto 0;
    background: rgba(255,255,255,0.2);
    border: 1.5px solid rgba(255,255,255,0.4);
    border-radius: 999px; padding: 0.5rem 1.6rem;
    display: inline-block; color: #fff !important;
    font-weight: 700; font-size: 0.85rem;
    backdrop-filter: blur(10px);
    text-shadow: 0 2px 4px rgba(0,0,0,0.15);
    width: fit-content; display: block;
}

@media (max-width: 768px) {
    .main-title  { font-size: 2.8rem; }
    .title-text  { font-size: 1.3rem; }
    .side-emoji  { display: none; }
    .card-header { flex-direction: column; align-items: flex-start; gap: 15px; }
    .loader-wrap { padding: 2rem 1.25rem; }
}
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------
# HERO
# ---------------------------------------------------
st.markdown("""
<div class="hero-section">
    <span class="hero-icon">🏛️</span>
    <div class="main-title">Sangha<span>Status</span></div>
    <div class="main-subtitle">
        A beautifully automated workspace for generating professional standup narratives, chat updates, and daily emails.
    </div>
    <div class="sangha-meaning">
        ✦ Sangha — the Pali word for "community" or "assembly" &nbsp;·&nbsp; Focusing on the Team ✦
    </div>
</div>
""", unsafe_allow_html=True)

# ---------------------------------------------------
# TEAM SIZE CARD
# ---------------------------------------------------
st.markdown("""
<div class="custom-card">
<div class="card-header">
<div class="card-title">
  <div class="icon-circle blue-icon">👥</div>
  <div>
    <div class="title-text">Team Size</div>
    <div class="desc-text">Select the total number of active team members for today.</div>
  </div>
</div>
<div class="side-emoji">📊</div>
</div>
""", unsafe_allow_html=True)

people_count = st.number_input(
    "Total active team members today",
    min_value=1, value=1, step=1,
    label_visibility="collapsed"
)
st.markdown("</div>", unsafe_allow_html=True)

# ---------------------------------------------------
# RAW UPDATES CARD
# ---------------------------------------------------
st.markdown("""
<div class="custom-card">
<div class="card-header">
<div class="card-title">
  <div class="icon-circle green-icon">📝</div>
  <div>
    <div class="title-text">Raw Updates</div>
    <div class="desc-text">Paste the raw daily updates from your team below.</div>
  </div>
</div>
<div class="side-emoji">📋</div>
</div>
""", unsafe_allow_html=True)

raw_updates = st.text_area(
    "Paste team updates below:",
    placeholder="""Alice:
- Working on API integration.
- Resolving backend issues.

Bob:
- Preparing test cases.
- Resolving deployment pipeline issues.
""",
    label_visibility="collapsed"
)
st.markdown("</div>", unsafe_allow_html=True)

# ---------------------------------------------------
# GENERATE BUTTON
# ---------------------------------------------------
generate = st.button("✨ Generate Professional Status")

if generate:
    if not raw_updates.strip():
        st.warning("⚠️ Please provide raw updates before generating.")
    else:
        total_stages = len(LOADER_STAGES)
        slot = st.empty()

        # Pre-API stages
        for i in range(3):
            slot.markdown(render_loader(i), unsafe_allow_html=True)
            time.sleep(0.55)

        # Stage 3 — show while API call runs
        slot.markdown(render_loader(3), unsafe_allow_html=True)

        try:
            current_date = datetime.now().strftime("%B %d, %Y")
            prompt_payload = f"""
Use this date for all sections: {current_date}
Team Members: {people_count}
Updates:
{raw_updates}
"""
            completion = client.chat.completions.create(
                model="nvidia/llama-3.3-nemotron-super-49b-v1",
                messages=[
                    {"role": "system", "content": SYSTEM_INSTRUCTIONS},
                    {"role": "user",   "content": prompt_payload}
                ],
                temperature=0.1,
                max_tokens=1500,
                response_format={"type": "json_object"}
            )

            generated_data = json.loads(completion.choices[0].message.content)

            # Post-API stages
            for i in range(4, total_stages):
                slot.markdown(render_loader(i), unsafe_allow_html=True)
                time.sleep(0.45)

            # Clear loader — reveal results
            slot.empty()
            st.markdown("<br>", unsafe_allow_html=True)

            # ── STANDUP NARRATIVE ──
            st.markdown("""
            <div class="colored-block narrative-block">
                <div class="block-title narrative-title">🗣️ Standup Narrative</div>
            """, unsafe_allow_html=True)
            st.code(generated_data.get("standup_narrative", "Error generating narrative."), language="text")
            st.markdown("</div>", unsafe_allow_html=True)

            # ── CHAT UPDATE ──
            st.markdown("""
            <div class="colored-block chat-block">
                <div class="block-title chat-title">💬 Chat Update</div>
            """, unsafe_allow_html=True)
            st.code(generated_data.get("chat_update", "Error generating chat update."), language="text")
            st.markdown("</div>", unsafe_allow_html=True)

            # ── EMAIL UPDATE ──
            st.markdown("""
            <div class="colored-block email-block">
                <div class="block-title email-title">📧 Email Update</div>
            """, unsafe_allow_html=True)
            st.code(generated_data.get("email_update", "Error generating email update."), language="text")
            st.markdown("</div>", unsafe_allow_html=True)

            # Token usage
            if hasattr(completion, "usage") and completion.usage is not None:
                st.markdown(
                    f'<div class="token-badge">🛡️ Tokens used this run: {completion.usage.total_tokens:,}</div>',
                    unsafe_allow_html=True
                )

        except json.JSONDecodeError:
            slot.empty()
            st.error("❌ The AI did not return a valid JSON format. Please try again.")
        except Exception as e:
            slot.empty()
            st.error(f"❌ Error generating response: {e}")