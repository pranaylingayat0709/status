# ---------------------------------------------------
# REPLACE ONLY THE CSS + HERO SECTION WITH THIS
# THIS MATCHES THE UI FROM THE IMAGE
# ---------------------------------------------------

# ---------------------------------------------------
# MODERN CSS
# ---------------------------------------------------

st.markdown("""
<style>

/* ------------------------------------------------ */
/* GOOGLE FONT */
/* ------------------------------------------------ */

@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

/* ------------------------------------------------ */
/* GLOBAL */
/* ------------------------------------------------ */

html, body, [class*="css"]  {
    font-family: 'Inter', sans-serif;
}

.stApp {

    background:
        radial-gradient(circle at top left, #edf4ff 0%, transparent 22%),
        radial-gradient(circle at bottom right, #edf7ff 0%, transparent 22%),
        linear-gradient(135deg, #f8fbff 0%, #eef5ff 100%);

    min-height: 100vh;
}

/* ------------------------------------------------ */
/* MAIN CONTAINER */
/* ------------------------------------------------ */

.main .block-container {

    max-width: 1150px;

    padding-top: 1rem;

    padding-bottom: 3rem;
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
/* HERO */
/* ------------------------------------------------ */

.hero-section {

    text-align: center;

    margin-bottom: 2rem;
}

/* ------------------------------------------------ */
/* HERO ILLUSTRATION */
/* ------------------------------------------------ */

.hero-top-image {

    width: 120px;

    margin: auto;

    margin-bottom: 0.8rem;
}

.hero-top-image img {

    width: 100%;

    border-radius: 0px !important;

    box-shadow: none !important;
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

    font-size: 1.15rem;

    max-width: 700px;

    margin: auto;

    line-height: 1.7;

    margin-bottom: 3rem;
}

/* ------------------------------------------------ */
/* TEAM CARD */
/* ------------------------------------------------ */

.team-card {

    background: rgba(255,255,255,0.65);

    border: 1px solid #cfe0ff;

    border-radius: 26px;

    padding: 2rem;

    box-shadow:
        0 10px 30px rgba(37,99,235,0.05);

    margin-bottom: 1.8rem;

    position: relative;

    overflow: hidden;
}

/* ------------------------------------------------ */
/* GREEN CARD */
/* ------------------------------------------------ */

.update-card {

    background: rgba(240,255,248,0.72);

    border: 1px solid #cceedd;

    border-radius: 26px;

    padding: 2rem;

    box-shadow:
        0 10px 30px rgba(15,23,42,0.04);

    margin-bottom: 2rem;

    position: relative;

    overflow: hidden;
}

/* ------------------------------------------------ */
/* CARD TITLE */
/* ------------------------------------------------ */

.card-title {

    display: flex;

    align-items: center;

    gap: 14px;

    font-size: 1.7rem;

    font-weight: 700;

    color: #0f172a;

    margin-bottom: 0.5rem;
}

/* ------------------------------------------------ */
/* CARD DESCRIPTION */
/* ------------------------------------------------ */

.card-description {

    color: #5b6477;

    font-size: 1rem;

    margin-bottom: 1.5rem;
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

    font-size: 1.7rem;

    flex-shrink: 0;
}

.blue-icon {

    background: #e9f1ff;
}

.green-icon {

    background: #dcfce7;
}

/* ------------------------------------------------ */
/* INPUTS */
/* ------------------------------------------------ */

.stNumberInput input,
.stTextArea textarea {

    background: rgba(255,255,255,0.95) !important;

    border: 2px solid #d6e5ff !important;

    border-radius: 18px !important;

    color: #0f172a !important;

    font-size: 1rem !important;

    padding: 1rem !important;

    box-shadow: none !important;
}

/* ------------------------------------------------ */
/* TEXT AREA */
/* ------------------------------------------------ */

.stTextArea textarea {

    min-height: 250px !important;

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

    box-shadow:
        0 10px 30px rgba(59,92,255,0.25);

    transition: all 0.3s ease !important;

    display: block;

    margin: auto;
}

.stButton > button:hover {

    transform: translateY(-2px);

    box-shadow:
        0 16px 35px rgba(59,92,255,0.35);
}

/* ------------------------------------------------ */
/* OUTPUT CARD */
/* ------------------------------------------------ */

.output-card {

    background: rgba(255,255,255,0.85);

    border-radius: 24px;

    padding: 2rem;

    box-shadow:
        0 15px 35px rgba(15,23,42,0.06);

    margin-top: 2rem;
}

/* ------------------------------------------------ */
/* MOBILE */
/* ------------------------------------------------ */

@media (max-width: 768px) {

    .main-title {
        font-size: 2.5rem;
    }

    .card-title {
        font-size: 1.3rem;
    }

    .hero-top-image {
        width: 85px;
    }
}

</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------
# HERO
# ---------------------------------------------------

st.markdown("""
<div class="hero-section">
""", unsafe_allow_html=True)

# SMALL TOP ILLUSTRATION

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
beautifully consolidated.
</div>
""", unsafe_allow_html=True)

st.markdown("</div>", unsafe_allow_html=True)

# ---------------------------------------------------
# TEAM CARD
# ---------------------------------------------------

st.markdown("""
<div class="team-card">

<div style="display:flex; align-items:center; justify-content:space-between; gap:20px; flex-wrap:wrap;">

<div style="flex:1; min-width:300px;">

<div class="card-title">

<div class="icon-circle blue-icon">
👥
</div>

<div>
Team Configuration
</div>

</div>

<div class="card-description">
Set the total number of active team members today.
</div>

</div>

<div style="font-size:70px; opacity:0.85;">
👨‍💻👩‍💻👨‍💻
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
# UPDATE CARD
# ---------------------------------------------------

st.markdown("""
<div class="update-card">

<div style="display:flex; align-items:center; justify-content:space-between; gap:20px; flex-wrap:wrap;">

<div style="flex:1; min-width:300px;">

<div class="card-title">

<div class="icon-circle green-icon">
📝
</div>

<div>
Raw Team Updates
</div>

</div>

<div class="card-description">
Paste the raw updates from your team below.
</div>

</div>

<div style="font-size:75px; opacity:0.85;">
📋
</div>

</div>
""", unsafe_allow_html=True)

raw_updates = st.text_area(
    "Paste team updates below:",
    placeholder="""Example:

Pranay:
- Working on masking enhancements.
- Resolving backend issues.

Devyanshi:
- Preparing test cases.
- Resolving share certificate issues.
"""
)

st.markdown("</div>", unsafe_allow_html=True)

# ---------------------------------------------------
# BUTTON
# ---------------------------------------------------

generate = st.button("✨ Generate Professional Status")