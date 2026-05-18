import streamlit as st
import json
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
# SYSTEM PROMPT (UPDATED FOR FULL SENTENCES)
# ---------------------------------------------------

SYSTEM_INSTRUCTIONS = """
You are PrashantStatus, a precise professional assistant.

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
  "standup_narrative": "Good morning, everyone.\\n\\nHere is the status update for [Insert Provided Date].\\n\\nStarting with [Name 1], he/she is currently focused on [Rewrite task into narrative].\\n\\nMoving on to [Name 2], he/she is progressing with [Rewrite task into narrative].\\n\\nFinally, [Name 3] is concentrating on [Rewrite task into narrative].\\n\\nThat concludes today’s status update.",
  
  "chat_update": "Daily Project Status Update | [Insert Provided Date]\\n\\n• [Name 1]\\n- [Expanded, complete professional sentence for Task 1].\\n- [Expanded, complete professional sentence for Task 2].\\n\\n• [Name 2]\\n- [Expanded, complete professional sentence for Task 1].",
  
  "email_update": "Subject: Daily Project Status Update | [Insert Provided Date]\\n\\nDear Team,\\n\\nI am writing to share the status for the activities performed on [Insert Provided Date].\\n\\n[Name 1]\\n- [Expanded, complete professional sentence for Task 1].\\n- [Expanded, complete professional sentence for Task 2].\\n\\n[Name 2]\\n- [Expanded, complete professional sentence for Task 1].\\n\\nLet me know in case you need more details.\\n\\nRegards,\\n[Name]"
}
"""

# ---------------------------------------------------
# CUSTOM CSS (VIBRANT AURORA THEME)
# ---------------------------------------------------

st.markdown("""
<style>

@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800;900&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

/* ------------------------------------------------ */
/* ANIMATED VIBRANT BACKGROUND */
/* ------------------------------------------------ */

@keyframes gradientBG {
    0% { background-position: 0% 50%; }
    50% { background-position: 100% 50%; }
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

#MainMenu, footer, header {
    visibility: hidden;
}

/* ------------------------------------------------ */
/* HERO SECTION (WHITE TEXT TO POP ON GRADIENT) */
/* ------------------------------------------------ */

.hero-section {
    text-align: center;
    margin-bottom: 3.5rem;
}

.hero-top-image {
    width: 110px;
    margin: auto;
    margin-bottom: 1.5rem;
    filter: drop-shadow(0 15px 20px rgba(0,0,0,0.2));
}

.hero-top-image img {
    width: 100%;
}

.main-title {
    font-size: 4rem;
    font-weight: 900;
    color: #ffffff !important;
    letter-spacing: -1.5px;
    margin-bottom: 0.5rem;
    text-shadow: 0 10px 20px rgba(0,0,0,0.15);
}

.main-title span {
    color: #ffde59 !important; /* Bright Yellow/Gold */
}

.main-subtitle {
    color: rgba(255, 255, 255, 0.95) !important;
    font-size: 1.25rem;
    font-weight: 600;
    max-width: 650px;
    margin: auto;
    line-height: 1.6;
    text-shadow: 0 4px 10px rgba(0,0,0,0.1);
}

/* ------------------------------------------------ */
/* SOLID WHITE GLASS CARDS */
/* ------------------------------------------------ */

.custom-card {
    background: rgba(255, 255, 255, 0.95);
    border-radius: 28px;
    padding: 2.5rem;
    box-shadow: 0 20px 50px rgba(0, 0, 0, 0.2);
    margin-bottom: 2rem;
    border: 1px solid rgba(255, 255, 255, 1);
    backdrop-filter: blur(20px);
}

.card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 1.5rem;
}

.card-title {
    display: flex;
    align-items: center;
    gap: 20px;
}

.icon-circle {
    width: 65px;
    height: 65px;
    border-radius: 20px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1.8rem;
    box-shadow: 0 8px 15px rgba(0,0,0,0.08);
}

/* Highly saturated card icons */
.blue-icon { background: #3b82f6; color: white; }
.green-icon { background: #10b981; color: white; }

.title-text {
    font-size: 1.6rem;
    font-weight: 800;
    color: #0f172a;
}

.desc-text {
    color: #475569;
    font-size: 1rem;
    margin-top: 0.3rem;
}

.side-emoji {
    font-size: 50px;
}

/* ------------------------------------------------ */
/* BOLD INPUTS */
/* ------------------------------------------------ */

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

.stTextArea textarea {
    min-height: 250px !important;
    line-height: 1.8 !important;
}

.stNumberInput input:focus, .stTextArea textarea:focus {
    border-color: #e73c7e !important;
    box-shadow: 0 0 0 4px rgba(231, 60, 126, 0.2) !important;
}

/* ------------------------------------------------ */
/* VIBRANT GRADIENT BUTTON */
/* ------------------------------------------------ */

.stButton > button {
    background: linear-gradient(135deg, #FF0076 0%, #590FB7 100%) !important;
    color: white !important;
    border: none !important;
    border-radius: 50px !important;
    padding: 1.2rem 4rem !important;
    font-size: 1.2rem !important;
    font-weight: 800 !important;
    letter-spacing: 1px;
    display: block;
    margin: 2.5rem auto;
    box-shadow: 0 10px 25px rgba(89, 15, 183, 0.4) !important;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
}

.stButton > button:hover {
    transform: translateY(-5px) scale(1.02);
    box-shadow: 0 15px 35px rgba(255, 0, 118, 0.5) !important;
}

/* ------------------------------------------------ */
/* HIGH-CONTRAST OUTPUT CONTAINERS */
/* ------------------------------------------------ */

.colored-block {
    padding: 2rem;
    border-radius: 24px;
    margin-bottom: 2rem;
    background: #ffffff;
    box-shadow: 0 10px 30px rgba(0,0,0,0.06);
    position: relative;
    overflow: hidden;
}

/* Bright Side Borders */
.narrative-block { border-left: 8px solid #4f46e5; background: rgba(79, 70, 229, 0.03); }
.chat-block { border-left: 8px solid #ec4899; background: rgba(236, 72, 153, 0.03); }
.email-block { border-left: 8px solid #f59e0b; background: rgba(245, 158, 11, 0.03); }

.block-title {
    font-size: 1.4rem;
    font-weight: 900;
    margin-bottom: 1.2rem;
    display: flex;
    align-items: center;
    gap: 12px;
}

.narrative-title { color: #4f46e5; }
.chat-title { color: #db2777; }
.email-title { color: #d97706; }

/* ------------------------------------------------ */
/* CODE BLOCKS (ST.CODE OVERRIDES) */
/* ------------------------------------------------ */

pre {
    border-radius: 16px !important;
    background: #ffffff !important;
    border: 2px solid rgba(0,0,0,0.05) !important;
    padding: 1.5rem !important;
    color: #0f172a !important;
    font-size: 1rem !important;
    box-shadow: inset 0 4px 10px rgba(0,0,0,0.02) !important;
}

@media (max-width: 768px) {
    .main-title { font-size: 2.8rem; }
    .title-text { font-size: 1.3rem; }
    .hero-top-image { width: 90px; }
    .side-emoji { display: none; }
    .card-header { flex-direction: column; align-items: flex-start; gap: 15px; }
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
A beautifully automated workspace for generating professional standup narratives, chat updates, and daily emails.
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
<div class="title-text">Team Size</div>
<div class="desc-text">Select the total number of active team members for today.</div>
</div>
</div>
<div class="side-emoji">📊</div>
</div>
""", unsafe_allow_html=True)

people_count = st.number_input(
    "Total active team members today",
    min_value=1,
    value=1,
    step=1,
    label_visibility="collapsed"
)
st.markdown("</div>", unsafe_allow_html=True)

# ---------------------------------------------------
# RAW TEAM UPDATES CARD
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
    placeholder="""Pranay:
- Working on masking enhancements.
- Resolving backend issues.

Devyanshi:
- Preparing test cases.
- Resolving share certificate issues.
""",
    label_visibility="collapsed"
)
st.markdown("</div>", unsafe_allow_html=True)

# ---------------------------------------------------
# BUTTON & GENERATION
# ---------------------------------------------------

generate = st.button("✨ Generate Professional Status")

if generate:
    if not raw_updates.strip():
        st.warning("⚠️ Please provide raw updates before generating.")
    else:
        with st.spinner("✨ Crafting your vibrant updates..."):
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
                    max_output_tokens=800,
                    response_mime_type="application/json" 
                )

                response = client.models.generate_content(
                    model="gemini-2.5-flash-lite", 
                    contents=contents,
                    config=config
                )
                
                # Parse the JSON response
                generated_data = json.loads(response.text)
                
                st.markdown("<br>", unsafe_allow_html=True)

                # NARRATIVE BLOCK (INDIGO)
                st.markdown("""
                <div class="colored-block narrative-block">
                    <div class="block-title narrative-title">🗣️ Standup Narrative</div>
                """, unsafe_allow_html=True)
                st.code(generated_data.get("standup_narrative", "Error generating narrative."), language="text")
                st.markdown("</div>", unsafe_allow_html=True)

                # CHAT BLOCK (PINK)
                st.markdown("""
                <div class="colored-block chat-block">
                    <div class="block-title chat-title">💬 Chat Update</div>
                """, unsafe_allow_html=True)
                st.code(generated_data.get("chat_update", "Error generating chat update."), language="text")
                st.markdown("</div>", unsafe_allow_html=True)

                # EMAIL BLOCK (AMBER)
                st.markdown("""
                <div class="colored-block email-block">
                    <div class="block-title email-title">📧 Email Update</div>
                """, unsafe_allow_html=True)
                st.code(generated_data.get("email_update", "Error generating email update."), language="text")
                st.markdown("</div>", unsafe_allow_html=True)
                
                # Usage Tracker
                if hasattr(response, 'usage_metadata'):
                    st.markdown(f"<p style='color: white; text-align: center; font-weight: bold; text-shadow: 0 2px 4px rgba(0,0,0,0.5);'>🛡️ Cost Guard Active: Used {response.usage_metadata.total_token_count} total tokens.</p>", unsafe_allow_html=True)

            except json.JSONDecodeError:
                st.error("❌ Error: The AI did not return a valid JSON format. Please try again.")
            except Exception as e:
                st.error(f"❌ Error generating response: {e}")