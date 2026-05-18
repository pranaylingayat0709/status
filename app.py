import streamlit as st
from google import genai
from google.genai import types

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
You are PrashantStatus.

Generate:
1. Standup Narrative
2. Chat Update
3. Daily Status Email

Keep responses:
- Professional
- Concise
- Well formatted
- Human sounding
"""

# ---------------------------------------------------
# CUSTOM CSS
# ---------------------------------------------------

st.markdown("""
<style>

/* ------------------------------------------------ */
/* IMPORT FONT */
/* ------------------------------------------------ */

@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

/* ------------------------------------------------ */
/* GLOBAL */
/* ------------------------------------------------ */

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

/* ------------------------------------------------ */
/* MAIN WIDTH */
/* ------------------------------------------------ */

.main .block-container {

    max-width: 1150px;

    padding-top: 1rem;

    padding-bottom: 4rem;
}

/* ------------------------------------------------ */
/* REMOVE STREAMLIT DEFAULT */
/* ------------------------------------------------ */

#MainMenu,
footer,
header {
    visibility: hidden;
}

/* ------------------------------------------------ */
/* HERO SECTION */
/* ------------------------------------------------ */

.hero-section {

    text-align: center;

    margin-bottom: 2.5rem;
}

/* ------------------------------------------------ */
/* HERO IMAGE */
/* ------------------------------------------------ */

.hero-top-image {

    width: 110px;

    margin: auto;

    margin-bottom: 1rem;
}

.hero-top-image img {

    width: 100%;
}

/* ------------------------------------------------ */
/* TITLE */
/* ------------------------------------------------ */

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

/* ------------------------------------------------ */
/* SUBTITLE */
/* ------------------------------------------------ */

.main-subtitle {

    color: #5b6477;

    font-size: 1.1rem;

    max-width: 700px;

    margin: auto;

    line-height: 1.7;

    margin-bottom: 3rem;
}

/* ------------------------------------------------ */
/* CARD */
/* ------------------------------------------------ */

.custom-card {

    background: rgba(255,255,255,0.75);

    border-radius: 28px;

    padding: 2rem;

    border: 1px solid rgba(207,224,255,0.8);

    box-shadow:
        0 10px 30px rgba(15,23,42,0.05);

    margin-bottom: 2rem;

    backdrop-filter: blur(10px);
}

/* ------------------------------------------------ */
/* GREEN CARD */
/* ------------------------------------------------ */

.green-card {

    background: rgba(240,255,248,0.78);

    border: 1px solid #d7f5e5;
}

/* ------------------------------------------------ */
/* CARD HEADER */
/* ------------------------------------------------ */

.card-header {

    display: flex;

    justify-content: space-between;

    align-items: center;

    gap: 20px;

    flex-wrap: wrap;

    margin-bottom: 1.5rem;
}

/* ------------------------------------------------ */
/* CARD TITLE */
/* ------------------------------------------------ */

.card-title {

    display: flex;

    align-items: center;

    gap: 16px;
}

/* ------------------------------------------------ */
/* ICON CIRCLE */
/* ------------------------------------------------ */

.icon-circle {

    width: 60px;

    height: 60px;

    border-radius: 50%;

    display: flex;

    align-items: center;

    justify-content: center;

    font-size: 1.6rem;
}

.blue-icon {

    background: #e9f1ff;
}

.green-icon {

    background: #dcfce7;
}

/* ------------------------------------------------ */
/* TEXT */
/* ------------------------------------------------ */

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

/* ------------------------------------------------ */
/* SIDE EMOJI */
/* ------------------------------------------------ */

.side-emoji {

    font-size: 75px;

    opacity: 0.9;
}

/* ------------------------------------------------ */
/* INPUT */
/* ------------------------------------------------ */

.stNumberInput input,
.stTextArea textarea {

    background: rgba(255,255,255,0.95) !important;

    border: 2px solid #dbeafe !important;

    border-radius: 18px !important;

    color: #0f172a !important;

    padding: 1rem !important;

    font-size: 1rem !important;

    box-shadow: none !important;
}

/* ------------------------------------------------ */
/* TEXT AREA */
/* ------------------------------------------------ */

.stTextArea textarea {

    min-height: 260px !important;

    line-height: 1.8 !important;
}

/* ------------------------------------------------ */
/* BUTTON */
/* ------------------------------------------------ */

.stButton > button {

    background:
        linear-gradient(
            135deg,
            #3b5cff 0%,
            #5b8cff 100%
        ) !important;

    color: white !important;

    border: none !important;

    border-radius: 50px !important;

    padding: 1rem 3rem !important;

    font-size: 1.1rem !important;

    font-weight: 700 !important;

    display: block;

    margin: auto;

    box-shadow:
        0 12px 30px rgba(59,92,255,0.25);

    transition: all 0.3s ease !important;
}

.stButton > button:hover {

    transform: translateY(-2px);

    box-shadow:
        0 18px 35px rgba(59,92,255,0.35);
}

/* ------------------------------------------------ */
/* OUTPUT CARD */
/* ------------------------------------------------ */

.output-card {

    background: rgba(255,255,255,0.88);

    border-radius: 28px;

    padding: 2rem;

    box-shadow:
        0 15px 40px rgba(15,23,42,0.08);

    margin-top: 2rem;
}

/* ------------------------------------------------ */
/* CODE BLOCK */
/* ------------------------------------------------ */

pre {

    border-radius: 18px !important;

    background: #eff6ff !important;

    border: 1px solid #dbeafe !important;

    padding: 1rem !important;
}

/* ------------------------------------------------ */
/* MOBILE */
/* ------------------------------------------------ */

@media (max-width: 768px) {

    .main-title {
        font-size: 2.5rem;
    }

    .title-text {
        font-size: 1.2rem;
    }

    .hero-top-image {
        width: 80px;
    }

    .side-emoji {
        font-size: 55px;
    }
}

</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------
# HERO SECTION
# ---------------------------------------------------

st.markdown("""
<div class="hero-section">
""", unsafe_allow_html=True)

# HERO IMAGE

st.markdown("""
<div class="hero-top-image">
<img src="https://cdn-icons-png.flaticon.com/512/4149/4149653.png">
</div>
""", unsafe_allow_html=True)

# TITLE

st.markdown("""
<div class="main-title">
✨ Prashant<span>Status</span>
</div>
""", unsafe_allow_html=True)

# SUBTITLE

st.markdown("""
<div class="main-subtitle">
Professional Standup Narratives, Chat Updates & Daily Status Emails,
beautifully consolidated into one elegant workspace.
</div>
""", unsafe_allow_html=True)

st.markdown("</div>", unsafe_allow_html=True)

# ---------------------------------------------------
# TEAM CONFIGURATION CARD
# ---------------------------------------------------

st.markdown("""
<div class="custom-card">

<div class="card-header">

<div class="card-title">

<div class="icon-circle blue-icon">
👥
</div>

<div>
<div class="title-text">Team Configuration</div>
<div class="desc-text">
Set the total number of active team members today.
</div>
</div>

</div>

<div class="side-emoji">
👨‍💻👩‍💻
</div>

</div>
""", unsafe_allow_html=True)

people_count = st.number_input(
    "Total active team members today",
    min_value=1,
    value=1,
    step=1
)

st.markdown("</div>", unsafe_allow_html=True)

# ---------------------------------------------------
# RAW TEAM UPDATES CARD
# ---------------------------------------------------

st.markdown("""
<div class="custom-card green-card">

<div class="card-header">

<div class="card-title">

<div class="icon-circle green-icon">
📝
</div>

<div>
<div class="title-text">Raw Team Updates</div>
<div class="desc-text">
Paste the raw updates from your team below.
</div>
</div>

</div>

<div class="side-emoji">
📋
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
"""
)

st.markdown("</div>", unsafe_allow_html=True)

# ---------------------------------------------------
# BUTTON
# ---------------------------------------------------

generate = st.button("✨ Generate Professional Status")

# ---------------------------------------------------
# GENERATE OUTPUT
# ---------------------------------------------------

if generate:

    if not raw_updates.strip():

        st.warning("⚠️ Please provide raw updates before generating.")

    else:

        with st.spinner("✨ Generating professional status updates..."):

            try:

                prompt_payload = f"""
Team Members: {people_count}

Updates:
{raw_updates}
"""

                contents = [
                    types.Content(
                        role="user",
                        parts=[
                            types.Part.from_text(
                                text=prompt_payload
                            )
                        ]
                    )
                ]

                config = types.GenerateContentConfig(
                    system_instruction=[
                        types.Part.from_text(
                            text=SYSTEM_INSTRUCTIONS
                        )
                    ]
                )

                response = client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=contents,
                    config=config
                )

                st.markdown("""
                <div class="output-card">
                """, unsafe_allow_html=True)

                st.markdown("## 📋 Generated Status Dashboard")

                st.markdown(response.text)

                st.markdown("</div>", unsafe_allow_html=True)

            except Exception as e:

                st.error(f"❌ Error generating response: {e}")