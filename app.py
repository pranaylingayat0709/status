import streamlit as st
import json
from openai import OpenAI
import requests
from streamlit_lottie import st_lottie
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
# LOTTIE ANIMATION HELPER
# ---------------------------------------------------
def load_lottieurl(url: str):
    r = requests.get(url)
    if r.status_code != 200:
        return None
    return r.json()

# Load a clean, abstract, slow-moving minimal blue wave loop
lottie_intro = load_lottieurl("https://lottie.host/80c4ab6c-5900-4ea2-8b65-68b449b28b7e/P5592hPz0z.json")

# ---------------------------------------------------
# API KEY CHECK
# ---------------------------------------------------
if "NVIDIA_API_KEY" not in st.secrets:
    st.error("🔑 NVIDIA_API_KEY not found in Streamlit secrets.")
    st.info("Please add NVIDIA_API_KEY to your Streamlit secrets to continue.")
    st.stop()

# ---------------------------------------------------
# NVIDIA NIM CLIENT
# ---------------------------------------------------
client = OpenAI(
  base_url="https://integrate.api.nvidia.com/v1",
  api_key=st.secrets["NVIDIA_API_KEY"]
)

# ---------------------------------------------------
# SYSTEM PROMPT (JSON STRICT FORMATTING)
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
  "standup_narrative": "Good morning, everyone.\\n\\nHere is the status update for [Insert Provided Date].\\n\\nStarting with [Name 1], he/she is currently focused on [Rewrite task into narrative].\\n\\nMoving on to [Name 2], he/she is progressing with [Rewrite task into narrative].\\n\\nThat concludes today’s status update.",
  
  "chat_update": "Daily Project Status Update | [Insert Provided Date]\\n\\n• [Name 1]\\n- [Expanded, complete professional sentence for Task 1].\\n- [Expanded, complete professional sentence for Task 2].\\n\\n• [Name 2]\\n- [Expanded, complete professional sentence for Task 1].",
  
  "email_update": "Subject: Daily Project Status Update | [Insert Provided Date]\\n\\nDear Team,\\n\\nI am writing to share the status for the activities performed on [Insert Provided Date].\\n\\n[Name 1]\\n- [Expanded, complete professional sentence for Task 1].\\n- [Expanded, complete professional sentence for Task 2].\\n\\n[Name 2]\\n- [Expanded, complete professional sentence for Task 1].\\n\\nLet me know in case you need more details.\\n\\nRegards,\\n[Name]"
}
"""

# ---------------------------------------------------
# CUSTOM CSS (Refined Apple-like + Colored Output Blocks)
# ---------------------------------------------------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

/* Global Reset */
html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

/* Subtle Premium Background */
.stApp {
    background-color: #f8fafc;
    background-image: radial-gradient(#cbd5e1 1px, transparent 1px);
    background-size: 24px 24px;
    min-height: 100vh;
}

/* Centered Content Container */
.main .block-container {
    max-width: 900px;
    padding-top: 2rem;
    padding-bottom: 4rem;
}

/* Hide Default Streamlit UI */
#MainMenu, footer, header { visibility: hidden; }

/* Smooth Fade-In Animation */
.stApp .block-container * {
    animation: fadeIn 0.8s ease-in-out forwards;
}
@keyframes fadeIn {
    from { opacity: 0; transform: translateY(10px); }
    to { opacity: 1; transform: translateY(0); }
}

/* Hero Section Typography */
.hero-section { text-align: center; margin-bottom: 2rem; }
.main-title {
    font-size: 3.5rem; font-weight: 800; color: #0f172a;
    letter-spacing: -1.5px; margin-bottom: 0.5rem; margin-top: -1rem;
}
.main-title span { color: #2563eb; }
.main-subtitle {
    color: #475569; font-size: 1.1rem; max-width: 600px;
    margin: auto; line-height: 1.6; margin-bottom: 2rem;
}

/* Clean White Input Cards */
.custom-card {
    background-color: #ffffff; border-radius: 16px; padding: 2rem;
    box-shadow: 0 4px 6px -1px rgba(15, 23, 42, 0.05);
    border: 1px solid #e2e8f0; margin-bottom: 1.5rem; transition: all 0.3s ease;
}
.custom-card:hover { box-shadow: 0 10px 15px -3px rgba(15, 23, 42, 0.08); }

/* Card Headers */
.card-title { display: flex; align-items: center; gap: 12px; margin-bottom: 1rem; }
.icon-circle { font-size: 1.5rem; }
.title-text { font-size: 1.25rem; font-weight: 700; color: #0f172a; }

/* Native Input Styling */
.stNumberInput input, .stTextArea textarea {
    background-color: #f8fafc !important; border: 1px solid #cbd5e1 !important;
    border-radius: 12px !important; color: #0f172a !important;
    padding: 0.75rem 1rem !important; font-size: 1rem !important;
}
.stNumberInput input:focus, .stTextArea textarea:focus {
    border-color: #3b82f6 !important; box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1) !important;
}

/* Animated Primary Button */
div.stButton > button:first-child { 
    background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%) !important;
    color: #ffffff !important; border-radius: 30px !important; border: none !important;
    padding: 0.75rem 3rem !important; font-weight: 600 !important; font-size: 1.1rem !important;
    display: block !important; margin: 2rem auto 0 auto !important; transition: all 0.3s ease !important;
    box-shadow: 0 4px 12px rgba(37, 99, 235, 0.2) !important;
}
div.stButton > button:first-child:hover {
    transform: translateY(-2px); box-shadow: 0 8px 20px rgba(37, 99, 235, 0.3) !important;
}

/* ------------------------------------------------ */
/* HIGH-CONTRAST OUTPUT CONTAINERS (From earlier code) */
/* ------------------------------------------------ */
.colored-block {
    padding: 2rem; border-radius: 16px; margin-bottom: 1.5rem;
    background: #ffffff; box-shadow: 0 4px 15px rgba(0,0,0,0.05);
}
.narrative-block { border-left: 6px solid #4f46e5; }
.chat-block { border-left: 6px solid #ec4899; }
.email-block { border-left: 6px solid #f59e0b; }

.block-title {
    font-size: 1.25rem; font-weight: 800; margin-bottom: 1rem;
    display: flex; align-items: center; gap: 10px;
}
.narrative-title { color: #4f46e5; }
.chat-title { color: #db2777; }
.email-title { color: #d97706; }

/* Clean Code Blocks */
pre {
    border-radius: 12px !important; background: #f8fafc !important;
    border: 1px solid #e2e8f0 !important; padding: 1.5rem !important; color: #0f172a !important;
}
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------
# ANIMATED HERO SECTION
# ---------------------------------------------------
st.markdown('<div class="hero-section">', unsafe_allow_html=True)

if lottie_intro:
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st_lottie(lottie_intro, speed=0.7, reverse=False, loop=True, quality="high", height=140)
else:
    st.markdown('<div class="hero-top-image"><img src="https://cdn-icons-png.flaticon.com/512/4149/4149653.png"></div>', unsafe_allow_html=True)

st.markdown('<div class="main-title">Prashant<span>Status</span></div>', unsafe_allow_html=True)
st.markdown('<div class="main-subtitle">Professional status updates consolidated into standup narratives, chat, and emails.</div>', unsafe_allow_html=True)
st.markdown("</div>", unsafe_allow_html=True)

# ---------------------------------------------------
# CONFIGURATION INPUTS
# ---------------------------------------------------
st.markdown("""
<div class="custom-card">
    <div class="card-title"><div class="icon-circle">👥</div><div class="title-text">Workspace Parameters</div></div>
""", unsafe_allow_html=True)
people_count = st.number_input("Total active team members today:", min_value=1, value=1, step=1, label_visibility="collapsed")
st.markdown("</div>", unsafe_allow_html=True)

st.markdown("""
<div class="custom-card">
    <div class="card-title"><div class="icon-circle">📝</div><div class="title-text">Raw Update Intake</div></div>
""", unsafe_allow_html=True)
raw_updates = st.text_area("Paste team notes below:", placeholder="Example:\nPranay:\n- Fixing backend version mismatches.", label_visibility="collapsed")
st.markdown("</div>", unsafe_allow_html=True)

# ---------------------------------------------------
# GENERATION TRIGGERS
# ---------------------------------------------------
if st.button("✦ Compile Professional Updates"):
    if not raw_updates.strip():
        st.warning("⚠️ Please provide raw updates before generating.")
    else:
        with st.spinner("✨ Processing via NVIDIA Nemotron JSON formatting..."):
            try:
                # Inject Live Date natively into the prompt
                current_date = datetime.now().strftime("%B %d, %Y")
                prompt_payload = f"Use this date for all sections: {current_date}\nTeam Members: {people_count}\nUpdates:\n{raw_updates}"

                # Execute NVIDIA NIM API Call using JSON enforcement
                completion = client.chat.completions.create(
                  model="nvidia/llama-3.3-nemotron-super-49b-v1",
                  messages=[
                    {"role": "system", "content": SYSTEM_INSTRUCTIONS},
                    {"role": "user", "content": prompt_payload}
                  ],
                  temperature=0.1, # Extremely low temperature for strict JSON adherence
                  max_tokens=4096,
                  response_format={"type": "json_object"} # Forces strict JSON output
                )

                response_text = completion.choices[0].message.content
                
                # Parse the JSON response
                generated_data = json.loads(response_text)
                
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
                
                # Token Usage Tracker (Mapped to OpenAI's token format)
                if hasattr(completion, 'usage') and completion.usage is not None:
                    total_tokens = completion.usage.total_tokens
                    st.markdown(f"<p style='color: #475569; text-align: center; font-size: 0.9rem;'>🛡️ Usage Tracker: Processed {total_tokens} total tokens.</p>", unsafe_allow_html=True)

            except json.JSONDecodeError:
                st.error("❌ Error: The AI did not return a valid JSON format. Please try generating again.")
            except Exception as e:
                st.error(f"❌ Error generating response: {e}")