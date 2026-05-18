# ---------------------------------------------------
# IMPORTS (YOU MISSED THIS)
# ---------------------------------------------------

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

Keep responses professional and concise.
"""

# ---------------------------------------------------
# CSS
# ---------------------------------------------------

st.markdown("""
<style>

/* -------------------- */
/* GLOBAL */
/* -------------------- */

.stApp {
    background: linear-gradient(
        135deg,
        #f8fbff 0%,
        #edf4ff 50%,
        #e4efff 100%
    );
    font-family: 'Inter', sans-serif;
}

/* -------------------- */
/* MAIN WIDTH */
/* -------------------- */

.main .block-container {
    max-width: 980px;
    padding-top: 1.2rem;
    padding-bottom: 3rem;
}

/* -------------------- */
/* REMOVE STREAMLIT */
/* -------------------- */

#MainMenu,
footer,
header {
    visibility: hidden;
}

/* -------------------- */
/* HERO */
/* -------------------- */

.hero-section {
    text-align: center;
    margin-bottom: 2rem;
}

/* -------------------- */
/* IMAGE */
/* -------------------- */

.hero-image img {

    width: 100%;

    max-height: 220px !important;

    object-fit: cover;

    border-radius: 24px;

    box-shadow:
        0 10px 25px rgba(37,99,235,0.12);
}

/* -------------------- */
/* TITLE */
/* -------------------- */

.main-title {

    font-size: 3.3rem;

    font-weight: 800;

    color: #0f172a;

    margin-top: 1.2rem;

    margin-bottom: 0.3rem;
}

/* -------------------- */
/* SUBTITLE */
/* -------------------- */

.main-subtitle {

    color: #475569;

    font-size: 1.05rem;

    margin-bottom: 2.2rem;
}

/* -------------------- */
/* MODERN CARD */
/* -------------------- */

.modern-card {

    background: rgba(255,255,255,0.82);

    border-radius: 22px;

    padding: 1.5rem;

    border: 1px solid #dbeafe;

    box-shadow:
        0 10px 25px rgba(15,23,42,0.05);

    margin-bottom: 1.5rem;
}

/* -------------------- */
/* CARD HEADINGS */
/* -------------------- */

.section-title {

    font-size: 1.2rem;

    font-weight: 700;

    color: #0f172a;

    margin-bottom: 1rem;
}

/* -------------------- */
/* NUMBER INPUT */
/* -------------------- */

.stNumberInput input {

    background: white !important;

    border: 2px solid #dbeafe !important;

    border-radius: 16px !important;

    color: #0f172a !important;
}

/* -------------------- */
/* TEXT AREA */
/* -------------------- */

.stTextArea textarea {

    background: white !important;

    border: 2px solid #dbeafe !important;

    border-radius: 18px !important;

    color: #0f172a !important;

    padding: 1rem !important;

    min-height: 240px !important;

    line-height: 1.7 !important;
}

/* -------------------- */
/* BUTTON */
/* -------------------- */

.stButton > button {

    background: linear-gradient(
        135deg,
        #2563eb 0%,
        #3b82f6 100%
    ) !important;

    color: white !important;

    border: none !important;

    border-radius: 50px !important;

    padding: 0.9rem 2.8rem !important;

    font-size: 1rem !important;

    font-weight: 700 !important;

    display: block;

    margin: auto;

    box-shadow:
        0 10px 25px rgba(37,99,235,0.2);

    transition: all 0.3s ease !important;
}

.stButton > button:hover {

    transform: translateY(-2px);

    box-shadow:
        0 15px 35px rgba(37,99,235,0.28);
}

/* -------------------- */
/* OUTPUT */
/* -------------------- */

.output-card {

    background: rgba(255,255,255,0.9);

    border-radius: 22px;

    padding: 2rem;

    margin-top: 2rem;

    box-shadow:
        0 15px 35px rgba(15,23,42,0.08);
}

/* -------------------- */
/* MOBILE */
/* -------------------- */

@media (max-width: 768px) {

    .main-title {
        font-size: 2.2rem;
    }

    .hero-image img {
        max-height: 170px !important;
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

# SMALL IMAGE

st.markdown('<div class="hero-image">', unsafe_allow_html=True)

st.image(
    "https://images.unsplash.com/photo-1522202176988-66273c2fd55f?q=80&w=1200&auto=format&fit=crop",
    use_container_width=True
)

st.markdown("</div>", unsafe_allow_html=True)

# TITLE

st.markdown("""
<div class="main-title">
✨ PrashantStatus
</div>
""", unsafe_allow_html=True)

# SUBTITLE

st.markdown("""
<div class="main-subtitle">
Professional Standup Narratives, Chat Updates & Daily Status Emails beautifully consolidated into one elegant workspace.
</div>
""", unsafe_allow_html=True)

st.markdown("</div>", unsafe_allow_html=True)

# ---------------------------------------------------
# TEAM CONFIG CARD
# ---------------------------------------------------

st.markdown("""
<div class="modern-card">
<div class="section-title">
👥 Team Configuration
</div>
""", unsafe_allow_html=True)

people_count = st.number_input(
    "Total active team members today:",
    min_value=1,
    value=1,
    step=1
)

st.markdown("</div>", unsafe_allow_html=True)

# ---------------------------------------------------
# RAW UPDATE CARD
# ---------------------------------------------------

st.markdown("""
<div class="modern-card">
<div class="section-title">
📝 Raw Team Updates
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
# OUTPUT
# ---------------------------------------------------

if generate:

    if not raw_updates.strip():

        st.warning("⚠️ Please provide raw updates.")

    else:

        with st.spinner("✨ Generating status updates..."):

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

                st.error(f"❌ Error: {e}")