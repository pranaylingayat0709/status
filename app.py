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
# SYSTEM PROMPT
# ---------------------------------------------------

SYSTEM_INSTRUCTIONS = """
You are PrashantStatus, a precise professional assistant.

STRICT RULES FOR FORMATTING (CRITICAL):
- DO NOT combine, merge, or summarize sentences. 
- You MUST write complete, grammatically correct sentences for every single subtask.
- ALWAYS use a standard hyphen "-" for bullet points in the Chat and Email updates. Do not use asterisks or dots for tasks.
- Keep each person's updates strictly separated under their name.
- DO NOT add any introductory or concluding conversational text. 
- You MUST output a valid JSON object with EXACTLY three keys: "standup_narrative", "chat_update", and "email_update".

EXPECTED JSON STRUCTURE AND TEMPLATE:

{
  "standup_narrative": "Good morning, everyone.\\n\\nHere is the status update for [Insert Provided Date].\\n\\nStarting with [Name 1], he/she is currently focused on [task narrative].\\n\\nMoving on to [Name 2], he/she is progressing with [task narrative].\\n\\nFinally, [Name 3] is concentrating on [task narrative].\\n\\nThat concludes today’s status update.",
  
  "chat_update": "Daily Project Status Update | [Insert Provided Date]\\n\\n• [Name 1]\\n- [Task 1 written as a complete sentence].\\n- [Task 2 written as a complete sentence].\\n\\n• [Name 2]\\n- [Task 1 written as a complete sentence].",
  
  "email_update": "Subject: Daily Project Status Update | [Insert Provided Date]\\n\\nDear Team,\\n\\nI am writing to share the status for the activities performed on [Insert Provided Date].\\n\\n[Name 1]\\n- [Task 1 written as a complete sentence].\\n- [Task 2 written as a complete sentence].\\n\\n[Name 2]\\n- [Task 1 written as a complete sentence].\\n\\nLet me know in case you need more details.\\n\\nRegards,\\n[Name]"
}
"""

# ---------------------------------------------------
# CUSTOM CSS (LIGHT & PLEASANT THEME)
# ---------------------------------------------------

st.markdown("""
<style>

@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
    color: #334155;
}

/* Beautiful Soft Pastel Mesh Background */
.stApp {
    background-color: #f8fafc;
    background-image: 
        radial-gradient(at 10% 10%, hsla(228,100%,74%,0.15) 0px, transparent 50%),
        radial-gradient(at 90% 10%, hsla(189,100%,56%,0.15) 0px, transparent 50%),
        radial-gradient(at 50% 90%, hsla(355,100%,93%,0.2) 0px, transparent 50%);
    min-height: 100vh;
}

.main .block-container {
    max-width: 1000px; /* Slightly narrower for a more elegant read */
    padding-top: 2rem;
    padding-bottom: 4rem;
}

#MainMenu, footer, header {
    visibility: hidden;
}

/* Hero Section */
.hero-section {
    text-align: center;
    margin-bottom: 3rem;
}

.hero-top-image {
    width: 100px;
    margin: auto;
    margin-bottom: 1.5rem;
    filter: drop-shadow(0 10px 15px rgba(0,0,0,0.05));
}

.hero-top-image img {
    width: 100%;
}

.main-title {
    font-size: 3.5rem;
    font-weight: 800;
    color: #0f172a;
    letter-spacing: -1.5px;
    margin-bottom: 0.5rem;
}

.main-title span {
    background: linear-gradient(135deg, #6366f1 0%, #a855f7 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}

.main-subtitle {
    color: #64748b;
    font-size: 1.15rem;
    max-width: 600px;
    margin: auto;
    line-height: 1.6;
}

/* Cards */
.custom-card {
    background: rgba(255, 255, 255, 0.85);
    border-radius: 24px;
    padding: 2rem;
    border: 1px solid rgba(255, 255, 255, 0.4);
    box-shadow: 0 10px 30px rgba(15, 23, 42, 0.04), inset 0 1px 0 rgba(255,255,255,1);
    margin-bottom: 2rem;
    backdrop-filter: blur(12px);
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
    gap: 16px;
}

.icon-circle {
    width: 55px;
    height: 55px;
    border-radius: 16px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1.5rem;
    box-shadow: 0 4px 10px rgba(0,0,0,0.03);
}

.blue-icon { background: #eff6ff; color: #3b82f6; border: 1px solid #dbeafe; }
.green-icon { background: #f0fdf4; color: #10b981; border: 1px solid #d1fae5; }

.title-text {
    font-size: 1.4rem;
    font-weight: 700;
    color: #1e293b;
}

.desc-text {
    color: #64748b;
    font-size: 0.95rem;
    margin-top: 0.2rem;
}

.side-emoji {
    font-size: 45px;
    opacity: 0.8;
}

/* Premium Inputs */
.stNumberInput input, .stTextArea textarea {
    background-color: #ffffff !important;
    border: 1px solid #e2e8f0 !important;
    border-radius: 16px !important;
    color: #334155 !important;
    padding: 1.2rem !important;
    font-size: 1rem !important;
    box-shadow: inset 0 2px 4px rgba(0,0,0,0.02) !important;
    transition: all 0.2s ease !important;
}

.stTextArea textarea {
    min-height: 220px !important;
    line-height: 1.7 !important;
}

.stNumberInput input:focus, .stTextArea textarea:focus {
    border-color: #a855f7 !important;
    box-shadow: 0 0 0 4px rgba(168, 85, 247, 0.15) !important;
}

/* Main Button */
.stButton > button {
    background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%) !important;
    color: white !important;
    border: none !important;
    border-radius: 50px !important;
    padding: 1rem 3.5rem !important;
    font-size: 1.1rem !important;
    font-weight: 600 !important;
    letter-spacing: 0.5px;
    display: block;
    margin: 2rem auto;
    box-shadow: 0 8px 20px rgba(99, 102, 241, 0.25) !important;
    transition: all 0.3s ease !important;
}

.stButton > button:hover {
    transform: translateY(-3px);
    box-shadow: 0 12px 25px rgba(99, 102, 241, 0.35) !important;
}

/* Output Containers */
.colored-block {
    padding: 1.8rem;
    border-radius: 20px;
    margin-bottom: 1.5rem;
    background: #ffffff;
    box-shadow: 0 4px 15px rgba(0,0,0,0.03);
    border: 1px solid rgba(0,0,0,0.02);
}

.narrative-block { border-left: 6px solid #3b82f6; }
.chat-block { border-left: 6px solid #10b981; }
.email-block { border-left: 6px solid #f59e0b; }

.block-title {
    font-size: 1.2rem;
    font-weight: 700;
    margin-bottom: 1.2rem;
    display: flex;
    align-items: center;
    gap: 10px;
}

.narrative-title { color: #2563eb; }
.chat-title { color: #059669; }
.email-title { color: #d97706; }

/* Code Blocks */
pre {
    border-radius: 12px !important;
    background: #f8fafc !important;
    border: 1px solid #e2e8f0 !important;
    padding: 1.2rem !important;
    color: #334155 !important;
}

@media (max-width: 768px) {
    .main-title { font-size: 2.2rem; }
    .title-text { font-size: 1.2rem; }
    .hero-top-image { width: 80px; }
    .side-emoji { display: none; }
    .card-header { flex-direction: column; align-items: flex-start; gap: 10px; }
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
        with st.spinner("✨ Crafting your updates..."):
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

                # NARRATIVE BLOCK (BLUE)
                st.markdown("""
                <div class="colored-block narrative-block">
                    <div class="block-title narrative-title">🗣️ Standup Narrative</div>
                """, unsafe_allow_html=True)
                st.code(generated_data.get("standup_narrative", "Error generating narrative."), language="text")
                st.markdown("</div>", unsafe_allow_html=True)

                # CHAT BLOCK (GREEN)
                st.markdown("""
                <div class="colored-block chat-block">
                    <div class="block-title chat-title">💬 Chat Update</div>
                """, unsafe_allow_html=True)
                st.code(generated_data.get("chat_update", "Error generating chat update."), language="text")
                st.markdown("</div>", unsafe_allow_html=True)

                # EMAIL BLOCK (ORANGE)
                st.markdown("""
                <div class="colored-block email-block">
                    <div class="block-title email-title">📧 Email Update</div>
                """, unsafe_allow_html=True)
                st.code(generated_data.get("email_update", "Error generating email update."), language="text")
                st.markdown("</div>", unsafe_allow_html=True)
                
                # Usage Tracker
                if hasattr(response, 'usage_metadata'):
                    st.caption(f"🛡️ **Cost Guard Active:** Used {response.usage_metadata.total_token_count} total tokens. *(Highly Optimized)*")

            except json.JSONDecodeError:
                st.error("❌ Error: The AI did not return a valid JSON format. Please try again.")
            except Exception as e:
                st.error(f"❌ Error generating response: {e}")