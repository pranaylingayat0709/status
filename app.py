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
- Human sounding
- Beautifully formatted
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

/* ------------------------------------------------ */
/* BACKGROUND */
/* ------------------------------------------------ */

.stApp {

    background:
        radial-gradient(circle at top left, #dbeafe 0%, transparent 25%),
        radial-gradient(circle at bottom right, #d1fae5 0%, transparent 20%),
        radial-gradient(circle at center right, #ede9fe 0%, transparent 18%),
        linear-gradient(
            135deg,
            #f8fbff 0%,
            #eef5ff 35%,
            #f5f3ff 70%,
            #ecfeff 100%
        );

    min-height: 100vh;
}

/* ------------------------------------------------ */
/* MAIN WIDTH */
/* ------------------------------------------------ */

.main .block-container {

    max-width: 1180px;

    padding-top: 1rem;

    padding-bottom: 4rem;
}

/* ------------------------------------------------ */
/* REMOVE STREAMLIT */
/* ------------------------------------------------ */

#MainMenu,
footer,
header {
    visibility: hidden;
}

/* ------------------------------------------------ */
/* HERO SECTION */
/* ------------------------------------------------ */

.hero-wrapper {

    background: rgba(255,255,255,0.55);

    border-radius: 36px;

    padding: 2rem;

    border: 1px solid rgba(255,255,255,0.7);

    box-shadow:
        0 10px 40px rgba(15,23,42,0.05);

    backdrop-filter: blur(18px);

    margin-bottom: 2rem;
}

/* ------------------------------------------------ */
/* HERO IMAGE */
/* ------------------------------------------------ */

.hero-image img {

    width: 100%;

    max-height: 320px !important;

    object-fit: cover;

    border-radius: 28px;

    box-shadow:
        0 15px 40px rgba(59,92,255,0.10);
}

/* ------------------------------------------------ */
/* TITLE */
/* ------------------------------------------------ */

.main-title {

    text-align: center;

    font-size: 4.2rem;

    font-weight: 800;

    letter-spacing: -2px;

    margin-top: 2rem;

    margin-bottom: 0.6rem;

    color: #0f172a;
}

.main-title span {

    background: linear-gradient(
        135deg,
        #4f7cff,
        #7c3aed
    );

    -webkit-background-clip: text;

    -webkit-text-fill-color: transparent;
}

/* ------------------------------------------------ */
/* SUBTITLE */
/* ------------------------------------------------ */

.main-subtitle {

    text-align: center;

    color: #5b6477;

    font-size: 1.1rem;

    max-width: 760px;

    margin: auto;

    line-height: 1.8;

    margin-bottom: 2rem;
}

/* ------------------------------------------------ */
/* CARD */
/* ------------------------------------------------ */

.custom-card {

    background: rgba(255,255,255,0.65);

    border-radius: 30px;

    padding: 2rem;

    border: 1px solid rgba(255,255,255,0.7);

    box-shadow:
        0 12px 35px rgba(15,23,42,0.05);

    backdrop-filter: blur(14px);

    margin-bottom: 2rem;
}

/* ------------------------------------------------ */
/* TEAM CARD */
/* ------------------------------------------------ */

.team-card {

    background:
        linear-gradient(
            135deg,
            rgba(239,246,255,0.92),
            rgba(245,243,255,0.92)
        );
}

/* ------------------------------------------------ */
/* UPDATE CARD */
/* ------------------------------------------------ */

.update-card {

    background:
        linear-gradient(
            135deg,
            rgba(236,253,245,0.95),
            rgba(240,249,255,0.95)
        );
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
/* TITLE GROUP */
/* ------------------------------------------------ */

.title-group {

    display: flex;

    align-items: center;

    gap: 16px;
}

/* ------------------------------------------------ */
/* ICON */
/* ------------------------------------------------ */

.icon-circle {

    width: 65px;

    height: 65px;

    border-radius: 50%;

    display: flex;

    align-items: center;

    justify-content: center;

    font-size: 1.7rem;
}

.team-icon {

    background:
        linear-gradient(
            135deg,
            #dbeafe,
            #ede9fe
        );
}

.update-icon {

    background:
        linear-gradient(
            135deg,
            #d1fae5,
            #ccfbf1
        );
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

    color: #64748b;

    font-size: 1rem;

    margin-top: 0.25rem;
}

/* ------------------------------------------------ */
/* SIDE EMOJI */
/* ------------------------------------------------ */

.side-emoji {

    font-size: 80px;

    opacity: 0.9;
}

/* ------------------------------------------------ */
/* INPUTS */
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
            #4f7cff 0%,
            #7c3aed 100%
        ) !important;

    color: white !important;

    border: none !important;

    border-radius: 50px !important;

    padding: 1rem 3.2rem !important;

    font-size: 1.1rem !important;

    font-weight: 700 !important;

    display: block;

    margin: auto;

    box-shadow:
        0 15px 35px rgba(79,124,255,0.25);

    transition: all 0.3s ease !important;
}

.stButton > button:hover {

    transform: translateY(-2px);

    box-shadow:
        0 18px 45px rgba(79,124,255,0.35);
}

/* ------------------------------------------------ */
/* OUTPUT CARD */
/* ------------------------------------------------ */

.output-card {

    background: rgba(255,255,255,0.82);

    border-radius: 30px;

    padding: 2rem;

    backdrop-filter: blur(14px);

    box-shadow:
        0 18px 40px rgba(15,23,42,0.08);

    margin-top: 2rem;
}

/* ------------------------------------------------ */
/* CODE */
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

    .side-emoji {
        font-size: 55px;
    }

    .hero-image img {
        max-height: 220px !important;
    }
}

</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------
# HERO SECTION
# ---------------------------------------------------

st.markdown("""
<div class="hero-wrapper">
""", unsafe_allow_html=True)

# AI STYLE HERO IMAGE

st.markdown("""
<div class="hero-image">
<img src="https://images.unsplash.com/photo-1677442136019-21780ecad995?q=80&w=1600&auto=format&fit=crop">
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
beautifully consolidated into one elegant AI-powered workspace.
</div>
""", unsafe_allow_html=True)

st.markdown("</div>", unsafe_allow_html=True)

# ---------------------------------------------------
# TEAM CARD
# ---------------------------------------------------

st.markdown("""
<div class="custom-card team-card">

<div class="card-header">

<div class="title-group">

<div class="icon-circle team-icon">
👥
</div>

<div>

<div class="title-text">
Team Configuration
</div>

<div class="desc-text">
Set the total number of active team members today.
</div>

</div>

</div>

<div class="side-emoji">
💼
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
# RAW UPDATE CARD
# ---------------------------------------------------

st.markdown("""
<div class="custom-card update-card">

<div class="card-header">

<div class="title-group">

<div class="icon-circle update-icon">
📝
</div>

<div>

<div class="title-text">
Raw Team Updates
</div>

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