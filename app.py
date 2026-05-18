# ---------------------------------------------------
# REPLACE YOUR ENTIRE HERO + INPUT UI SECTION
# WITH THIS CLEAN MODERN VERSION
# ---------------------------------------------------

# ---------------------------------------------------
# MODERN CSS
# ---------------------------------------------------

st.markdown("""
<style>

/* -------------------- */
/* GLOBAL BACKGROUND */
/* -------------------- */

.stApp {
    background: linear-gradient(
        135deg,
        #f8fbff 0%,
        #edf4ff 50%,
        #e0ecff 100%
    );
    font-family: 'Inter', sans-serif;
}

/* -------------------- */
/* MAIN CONTAINER */
/* -------------------- */

.main .block-container {
    max-width: 1000px;
    padding-top: 1rem;
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
/* HERO SECTION */
/* -------------------- */

.hero-section {
    text-align: center;
    margin-bottom: 2rem;
}

/* -------------------- */
/* SMALL HERO IMAGE */
/* -------------------- */

.hero-image img {
    width: 100%;
    max-height: 240px !important;
    object-fit: cover;
    border-radius: 28px;
    box-shadow: 0 12px 30px rgba(37,99,235,0.12);
}

/* -------------------- */
/* TITLE */
/* -------------------- */

.main-title {
    font-size: 3.4rem;
    font-weight: 800;
    color: #0f172a;
    margin-top: 1.4rem;
    margin-bottom: 0.4rem;
    letter-spacing: -1.5px;
}

/* -------------------- */
/* SUBTITLE */
/* -------------------- */

.main-subtitle {
    font-size: 1.05rem;
    color: #475569;
    margin-bottom: 2.5rem;
}

/* -------------------- */
/* MODERN CARD */
/* -------------------- */

.modern-card {
    background: rgba(255,255,255,0.82);
    backdrop-filter: blur(10px);

    border-radius: 24px;

    padding: 1.5rem;

    border: 1px solid rgba(255,255,255,0.7);

    box-shadow:
        0 10px 25px rgba(15,23,42,0.06);

    margin-bottom: 1.5rem;
}

/* -------------------- */
/* SECTION TITLE */
/* -------------------- */

.section-title {
    font-size: 1.25rem;
    font-weight: 700;
    color: #0f172a;
    margin-bottom: 1rem;
}

/* -------------------- */
/* INPUT BOXES */
/* -------------------- */

.stTextArea textarea,
.stNumberInput input {

    background: #ffffff !important;

    border: 2px solid #dbeafe !important;

    border-radius: 18px !important;

    color: #0f172a !important;

    padding: 1rem !important;

    font-size: 1rem !important;

    box-shadow: none !important;
}

/* -------------------- */
/* TEXT AREA HEIGHT */
/* -------------------- */

.stTextArea textarea {
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

    box-shadow:
        0 10px 20px rgba(37,99,235,0.18);

    transition: all 0.3s ease !important;

    display: block;
    margin: auto;
}

.stButton > button:hover {

    transform: translateY(-2px);

    box-shadow:
        0 15px 30px rgba(37,99,235,0.28);
}

/* -------------------- */
/* OUTPUT */
/* -------------------- */

.output-card {

    background: rgba(255,255,255,0.9);

    border-radius: 24px;

    padding: 2rem;

    margin-top: 2rem;

    box-shadow:
        0 15px 40px rgba(15,23,42,0.08);
}

/* -------------------- */
/* RESPONSIVE */
/* -------------------- */

@media (max-width: 768px) {

    .main-title {
        font-size: 2.3rem;
    }

    .hero-image img {
        max-height: 180px !important;
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

# SMALLER IMAGE
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
# TEAM CONFIGURATION CARD
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
        st.warning("⚠️ Please provide raw updates before continuing.")
        st.stop()

    with st.spinner("✨ Generating beautifully structured status updates..."):

        try:

            prompt_payload = f"""
Total Team Members: {people_count}

Updates:
{raw_updates}
"""

            contents = [
                types.Content(
                    role="user",
                    parts=[
                        types.Part.from_text(text=prompt_payload)
                    ]
                )
            ]

            config = types.GenerateContentConfig(
                system_instruction=[
                    types.Part.from_text(text=SYSTEM_INSTRUCTIONS)
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
            st.error(f"❌ Error generating status: {e}")