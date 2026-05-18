import streamlit as st
from google import genai
from google.genai import types
from datetime import datetime

# ---------------------------------------------------
# PAGE CONFIG
# ---------------------------------------------------

st.set_page_config(
    page_title="PrashantStatus",
    page_icon="✨",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ---------------------------------------------------
# API KEY CHECK
# ---------------------------------------------------

if "GEMINI_API_KEY" not in st.secrets:
    st.error("🔑 GEMINI_API_KEY not found in Streamlit secrets.")
    st.stop()

# ---------------------------------------------------
# GEMINI CLIENT
# ---------------------------------------------------

client = genai.Client(
    api_key=st.secrets["GEMINI_API_KEY"]
)

# ---------------------------------------------------
# SYSTEM PROMPT
# ---------------------------------------------------

SYSTEM_INSTRUCTIONS = """
You are PrashantStatus, a precise professional assistant.

STRICT RULES FOR FORMATTING (CRITICAL):
- DO NOT combine, merge, or summarize sentences. 
- You MUST write complete, grammatically correct sentences for every single subtask.
- ALWAYS use a standard hyphen "-" for bullet points in the Chat and Email updates. Do not use asterisks or dots for tasks.
- Keep each person's updates strictly separated under their name.
- ALWAYS follow the EXACT layout and wording of the template below.
- DO NOT add any introductory or concluding conversational text. Output ONLY the filled template.

EXPECTED OUTPUT TEMPLATE:

# 🗣️ Standup Narrative

Good morning, everyone.

Here is the status update for [Insert Provided Date].

Starting with [Name 1], [he/she] is currently focused on [task narrative] and [task narrative].

Moving on to [Name 2], [he/she] is progressing with [task narrative] and [task narrative].

Finally, [Name 3] is concentrating on [task narrative].

That concludes today’s status update.

---

### 📋 Copy Chat Update

Daily Project Status Update | [Insert Provided Date]

• [Name 1]
- [Task 1 written as a complete sentence].
- [Task 2 written as a complete sentence].

• [Name 2]
- [Task 1 written as a complete sentence].
- [Task 2 written as a complete sentence].

---

### 📋 Copy Email Update

Subject: Daily Project Status Update | [Insert Provided Date]

Dear Team,

I am writing to share the status for the activities performed on [Insert Provided Date].

[Name 1]
- [Task 1 written as a complete sentence].
- [Task 2 written as a complete sentence].

[Name 2]
- [Task 1 written as a complete sentence].
- [Task 2 written as a complete sentence].

Let me know in case you need more details.

Regards,
[Name]
"""

# ---------------------------------------------------
# CUSTOM CSS
# ---------------------------------------------------

st.markdown("""
<style>

@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

.stApp {
    background:
        radial-gradient(circle at top left, #edf4ff 0%, transparent 25%),
        radial-gradient(circle at bottom right, #eef9ff 0%, transparent 25%),
        linear-gradient(135deg, #f8fbff 0%, #eef5ff 100%);
    min-height: 100vh;
}

.main .block-container {
    max-width: 1150px;
    padding-top: 1rem;
    padding-bottom: 4rem;
}

#MainMenu, footer, header {
    visibility: hidden;
}

.hero-section {
    text-align: center;
    margin-bottom: 2.5rem;
}

.hero-top-image {
    width: 110px;
    margin: auto;
    margin-bottom: 1rem;
}

.hero-top-image img {
    width: 100%;
}

.main-title {
    font-size: 4rem;
    font-weight: 800;
    color: #0f172a;
    letter-spacing: -2px;
    margin-bottom: 0.5rem;
}

.main-title span {
    color: #4f7cff;
}

.main-subtitle {
    color: #5b6477;
    font-size: 1.1rem;
    max-width: 700px;
    margin: auto;
    line-height: 1.7;
    margin-bottom: 3rem;
}

.custom-card {
    background: rgba(255,255,255,0.75);
    border-radius: 28px;
    padding: 2rem;
    border: 1px solid rgba(207,224,255,0.8);
    box-shadow: 0 10px 30px rgba(15,23,42,0.05);
    margin-bottom: 2rem;
    backdrop-filter: blur(10px);
}

.green-card {
    background: rgba(240,255,248,0.78);
    border: 1px solid #d7f5e5;
}

.card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 20px;
    flex-wrap: wrap;
    margin-bottom: 1.5rem;
}

.card-title {
    display: flex;
    align-items: center;
    gap: 16px;
}

.icon-circle {
    width: 60px;
    height: 60px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1.6rem;
}

.blue-icon { background: #e9f1ff; }
.green-icon { background: #dcfce7; }

.title-text {
    font-size: 1.6rem;
    font-weight: 700;
    color: #0f172a;
}

.desc-text {
    color: #5b6477;
    font-size: 1rem;
    margin-top: 0.2rem;
}

.side-emoji {
    font-size: 75px;
    opacity: 0.9;
}

.stNumberInput input, .stTextArea textarea {
    background: rgba(255,255,255,0.95) !important;
    border: 2px solid #dbeafe !important;
    border-radius: 18px !important;
    color: #0f172a !important;
    padding: 1rem !important;
    font-size: 1rem !important;
    box-shadow: none !important;
}

.stTextArea textarea {
    min-height: 260px !important;
    line-height: 1.8 !important;
}

.stButton > button {
    background: linear-gradient(135deg, #3b5cff 0%, #5b8cff 100%) !important;
    color: white !important;
    border: none !important;
    border-radius: 50px !important;
    padding: 1rem 3rem !important;
    font-size: 1.1rem !important;
    font-weight: 700 !important;
    display: block;
    margin: auto;
    box-shadow: 0 12px 30px rgba(59,92,255,0.25);
    transition: all 0.3s ease !important;
}

.stButton > button:hover {
    transform: translateY(-2px);
    box-shadow: 0 18px 35px rgba(59,92,255,0.35);
}

.output-card {
    background: rgba(255,255,255,0.88);
    border-radius: 28px;
    padding: 2rem;
    box-shadow: 0 15px 40px rgba(15,23,42,0.08);
    margin-top: 2rem;
}

pre {
    border-radius: 18px !important;
    background: #eff6ff !important;
    border: 1px solid #dbeafe !important;
    padding: 1rem !important;
}

@media (max-width: 768px) {
    .main-title { font-size: 2.5rem; }
    .title-text { font-size: 1.2rem; }
    .hero-top-image { width: 80px; }
    .side-emoji { font-size: 55px; }
}
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------
# HERO SECTION
# ---------------------------------------------------

st.markdown("""
<div class="hero-section">
<div class="hero-top-image">
<img src="https://cdn-icons-png.flaticon.com/512/4149/4149653.png">
</div>
<div class="main-title">✨ Prashant<span>Status</span></div>
<div class="main-subtitle">
Professional Standup Narratives, Chat Updates & Daily Status Emails,
beautifully consolidated into one elegant workspace.
</div>
</div>
""", unsafe_allow_html=True)

# ---------------------------------------------------
# TEAM CONFIGURATION CARD
# ---------------------------------------------------

st.markdown("""
<div class="custom-card">
<div class="card-header">
<div class="card-title">
<div class="icon-circle blue-icon">👥</div>
<div>
<div class="title-text">Team Configuration</div>
<div class="desc-text">Set the total number of active team members today.</div>
</div>
</div>
<div class="side-emoji">👨‍💻👩‍💻</div>
</div>
</div>
""", unsafe_allow_html=True)

people_count = st.number_input(
    "Total active team members today",
    min_value=1,
    value=1,
    step=1,
    label_visibility="collapsed"
)

# ---------------------------------------------------
# RAW TEAM UPDATES CARD
# ---------------------------------------------------

st.markdown("""
<div class="custom-card green-card">
<div class="card-header">
<div class="card-title">
<div class="icon-circle green-icon">📝</div>
<div>
<div class="title-text">Raw Team Updates</div>
<div class="desc-text">Paste the raw updates from your team below.</div>
</div>
</div>
<div class="side-emoji">📋</div>
</div>
</div>
""", unsafe_allow_html=True)

raw_updates = st.text_area(
    "Paste team updates below:",
    placeholder="""Pranay:
- Working on masking enhancements.
- Resolving backend issues.

Devyanshi:
- Preparing test cases.
- Resolving share certificate issues.

RamSagar:
- Fixing reported defects.
""",
    label_visibility="collapsed"
)

# ---------------------------------------------------
# BUTTON & GENERATION
# ---------------------------------------------------

generate = st.button("✨ Generate Professional Status")

if generate:
    if not raw_updates.strip():
        st.warning("⚠️ Please provide raw updates before generating.")
    else:
        with st.spinner("✨ Generating optimized status updates..."):
            try:
                current_date = datetime.now().strftime("%B %d, %Y")

                prompt_payload = f"""
Use this date for all sections: {current_date}
Team Members: {people_count}
Updates:
{raw_updates}
"""
                contents = [
                    types.Content(
                        role="user",
                        parts=[types.Part.from_text(text=prompt_payload)]
                    )
                ]

                config = types.GenerateContentConfig(
                    system_instruction=[
                        types.Part.from_text(text=SYSTEM_INSTRUCTIONS)
                    ],
                    temperature=0.1, 
                    max_output_tokens=600 # Tightly capped to prevent token bleed
                )

                response = client.models.generate_content(
                    model="gemini-2.5-flash-lite", # The most cost-efficient model
                    contents=contents,
                    config=config
                )

                st.markdown('<div class="output-card">', unsafe_allow_html=True)
                st.markdown(response.text)
                
                # Usage Tracker
                if hasattr(response, 'usage_metadata'):
                    st.caption(f"🛡️ **Cost Guard Active:** Used {response.usage_metadata.total_token_count} total tokens. *(Highly Optimized)*")
                
                st.markdown("</div>", unsafe_allow_html=True)

            except Exception as e:
                st.error(f"❌ Error generating response: {e}")