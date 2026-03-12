import streamlit as st
from sheets_db import load_settings, save_settings, load_team_members, save_team_members

st.set_page_config(page_title="Settings", layout="wide", page_icon="⚙️")
st.title("⚙️ Settings")

settings = load_settings()
team_members = load_team_members()

# ── COMPANY & REP ──────────────────────────────────────────────────────────────

st.subheader("🍗 Company & Rep Info")
st.caption("Used in every generated email, phone script, and brief.")

c1, c2 = st.columns(2)
company_name = c1.text_input("Company Name", value=settings.get("company_name", "Chick-fil-A Catering"))
company_location = c2.text_input("Location", value=settings.get("company_location", ""), placeholder="e.g. North San Antonio")

r1, r2, r3, r4 = st.columns(4)
rep_name = r1.text_input("Your Name", value=settings.get("rep_name", ""))
rep_title = r2.text_input("Your Title", value=settings.get("rep_title", "Catering Specialist"))
rep_email = r3.text_input("Your Email", value=settings.get("rep_email", ""))
rep_phone = r4.text_input("Your Phone", value=settings.get("rep_phone", ""))

st.markdown("---")

# ── TEAM MEMBERS ───────────────────────────────────────────────────────────────

st.subheader("👥 Team Members")
st.caption("Names appear in the 'Assigned To' dropdown in the Pipeline.")

members_text = st.text_area("One name per line", value="\n".join(team_members), height=120,
                             placeholder="John Smith\nJane Doe\nMike Johnson")

st.markdown("---")

# ── LEAD GEN DEFAULTS ──────────────────────────────────────────────────────────

st.subheader("🔍 Lead Search Defaults")
from config import CATEGORY_OPTIONS
d1, d2, d3 = st.columns(3)
default_zip = d1.text_input("Default ZIP", value=settings.get("default_zip", ""))
default_radius = d2.slider("Default Radius (miles)", 5, 30, int(settings.get("default_radius", 10)))
default_cat = settings.get("default_category", "school")
default_category = d3.selectbox("Default Category", CATEGORY_OPTIONS,
                                 index=CATEGORY_OPTIONS.index(default_cat) if default_cat in CATEGORY_OPTIONS else 0)

st.markdown("---")

# ── PIPELINE VALUES ────────────────────────────────────────────────────────────

st.subheader("💰 Pipeline Value Estimates")
st.caption("Used to estimate open pipeline value on the dashboard.")
p1, p2, p3 = st.columns(3)
pipeline_small = p1.number_input("Small Lead ($)", min_value=0, step=100, value=int(settings.get("pipeline_small", 500)))
pipeline_medium = p2.number_input("Medium Lead ($)", min_value=0, step=100, value=int(settings.get("pipeline_medium", 1000)))
pipeline_large = p3.number_input("Large Lead ($)", min_value=0, step=100, value=int(settings.get("pipeline_large", 2000)))

st.markdown("---")

# ── BRAND VOICE ────────────────────────────────────────────────────────────────

st.subheader("✍️ Brand Voice & Email Training")
st.caption("The AI uses this to write emails and scripts that sound like your team.")

brand_voice = st.text_area("Brand Voice Description", value=settings.get("brand_voice", ""), height=100,
                            placeholder="e.g. Direct, warm, and genuine. Get to the point fast. Sound like a person, not a press release.")

st.caption("Paste up to 3 real emails your team has sent — the AI will match their style exactly.")
e1 = st.text_area("Sample Email #1", value=settings.get("sample_email_1", ""), height=150,
                   placeholder="Paste a real outreach email here...")
e2 = st.text_area("Sample Email #2", value=settings.get("sample_email_2", ""), height=150,
                   placeholder="Optional...")
e3 = st.text_area("Sample Email #3", value=settings.get("sample_email_3", ""), height=150,
                   placeholder="Optional...")

st.markdown("---")

# ── SAVE ───────────────────────────────────────────────────────────────────────

if st.button("💾 Save All Settings", type="primary", use_container_width=True):
    new_settings = {
        "company_name": company_name,
        "company_location": company_location,
        "rep_name": rep_name,
        "rep_title": rep_title,
        "rep_email": rep_email,
        "rep_phone": rep_phone,
        "default_zip": default_zip,
        "default_radius": str(default_radius),
        "default_category": default_category,
        "pipeline_small": str(pipeline_small),
        "pipeline_medium": str(pipeline_medium),
        "pipeline_large": str(pipeline_large),
        "brand_voice": brand_voice,
        "sample_email_1": e1,
        "sample_email_2": e2,
        "sample_email_3": e3,
        "theme": settings.get("theme", "dark"),
    }
    new_members = [m.strip() for m in members_text.strip().split("\n") if m.strip()]

    with st.spinner("Saving..."):
        save_settings(new_settings)
        save_team_members(new_members)

    load_settings.clear()
    st.success("Settings saved.")
