import streamlit as st
from sheets_db import load_settings, save_settings, load_team_members, save_team_members, load_leads, delete_lead

st.set_page_config(page_title="Settings", layout="wide", page_icon="⚙️")
st.title("⚙️ Settings")

settings = load_settings()
team_members = load_team_members()

# ── THEME ──────────────────────────────────────────────────────────────────────

st.subheader("🎨 Theme")
st.caption("Changes apply after saving and refreshing the page.")

theme_choice = st.radio(
    "App Theme",
    ["Dark", "Light"],
    index=0 if settings.get("theme", "dark") == "dark" else 1,
    horizontal=True,
)

st.info("To apply the theme change: save below, then use the **⋮ menu → Settings → Theme** in the top-right corner of the app to switch between Dark and Light mode instantly.")

st.markdown("---")

# ── COMPANY & REP INFO ─────────────────────────────────────────────────────────

st.subheader("🍗 Company & Rep Info")
st.caption("Used in every generated email, phone script, and brief.")

ci1, ci2 = st.columns(2)
company_name = ci1.text_input("Company Name", value=settings.get("company_name", "Chick-fil-A Catering"))
company_location = ci2.text_input("Location / Operator", value=settings.get("company_location", ""), placeholder="e.g. North San Antonio")

ri1, ri2, ri3, ri4 = st.columns(4)
rep_name = ri1.text_input("Your Name", value=settings.get("rep_name", ""))
rep_title = ri2.text_input("Your Title", value=settings.get("rep_title", "Catering Specialist"))
rep_email = ri3.text_input("Your Email", value=settings.get("rep_email", ""))
rep_phone = ri4.text_input("Your Phone", value=settings.get("rep_phone", ""))

st.markdown("---")

# ── LEAD GENERATION DEFAULTS ───────────────────────────────────────────────────

st.subheader("🔍 Lead Generation Defaults")
st.caption("Pre-fill the Lead Generation page with your most common search settings.")

col1, col2, col3 = st.columns(3)
default_zip = col1.text_input("Default ZIP Code", value=settings.get("default_zip", ""))
default_radius = col2.slider("Default Radius (miles)", 5, 30, int(settings.get("default_radius", 10)))
category_options = ["school", "hospital", "church", "corporate office"]
default_category = col3.selectbox(
    "Default Category",
    category_options,
    index=category_options.index(settings.get("default_category", "school"))
    if settings.get("default_category", "school") in category_options else 0,
)

st.markdown("---")

# ── PIPELINE VALUE ESTIMATES ───────────────────────────────────────────────────

st.subheader("💰 Pipeline Value Estimates")
st.caption("Used on the Dashboard and Analytics page to estimate open pipeline value.")

vc1, vc2, vc3 = st.columns(3)
pipeline_small = vc1.number_input("Small Lead Value ($)", min_value=0, step=100, value=int(settings.get("pipeline_small", 500)))
pipeline_medium = vc2.number_input("Medium Lead Value ($)", min_value=0, step=100, value=int(settings.get("pipeline_medium", 1000)))
pipeline_large = vc3.number_input("Large Lead Value ($)", min_value=0, step=100, value=int(settings.get("pipeline_large", 2000)))

st.markdown("---")

# ── TEAM MEMBERS ───────────────────────────────────────────────────────────────

st.subheader("👥 Team Members")
st.caption("Names appear in the 'Assigned To' dropdown in the CRM Pipeline.")

members_text = st.text_area(
    "One name per line",
    value="\n".join(team_members),
    height=150,
    placeholder="John Smith\nJane Doe\nMike Johnson",
)

st.markdown("---")

# ── BRAND VOICE & EMAIL TRAINING ───────────────────────────────────────────────

st.subheader("✍️ Brand Voice & Email Training")
st.caption("The AI will use these to write emails and phone scripts that sound like your team — not a robot.")

brand_voice = st.text_area(
    "Brand Voice Description",
    value=settings.get("brand_voice", ""),
    height=120,
    placeholder="""Describe how your team communicates. Examples:
- We're direct, confident, and get to the point fast.
- We never use corporate jargon. We write like we talk.
- Our tone is friendly but professional — like a trusted advisor, not a vendor.
- We always lead with their problem, not our product.""",
)

st.caption("Paste up to 3 real emails your team has sent. The AI will match their style exactly.")

sample_email_1 = st.text_area(
    "Sample Email #1",
    value=settings.get("sample_email_1", ""),
    height=180,
    placeholder="Paste a real outreach email here (subject + body)...",
)
sample_email_2 = st.text_area(
    "Sample Email #2",
    value=settings.get("sample_email_2", ""),
    height=180,
    placeholder="Paste another real email here (optional)...",
)
sample_email_3 = st.text_area(
    "Sample Email #3",
    value=settings.get("sample_email_3", ""),
    height=180,
    placeholder="Paste another real email here (optional)...",
)

st.markdown("---")

# ── DANGER ZONE ────────────────────────────────────────────────────────────────

st.subheader("🚨 Danger Zone")

with st.expander("Reset All Leads"):
    st.warning("This will permanently delete ALL leads from the CRM. This cannot be undone.")
    if st.button("🗑️ Clear All Leads", type="secondary"):
        st.session_state["confirm_clear_all"] = True

    if st.session_state.get("confirm_clear_all"):
        st.error("Are you absolutely sure? All lead data will be lost.")
        cc1, cc2 = st.columns(2)
        if cc1.button("Yes, delete everything"):
            df = load_leads()
            with st.spinner("Deleting all leads..."):
                for _, row in df.iterrows():
                    delete_lead(row["place_id"])
            st.session_state["confirm_clear_all"] = False
            load_leads.clear()
            st.success("All leads cleared.")
            st.rerun()
        if cc2.button("Cancel"):
            st.session_state["confirm_clear_all"] = False
            st.rerun()

st.markdown("---")

# ── SAVE ───────────────────────────────────────────────────────────────────────

if st.button("💾 Save Settings", type="primary", use_container_width=True):
    new_settings = {
        "theme": theme_choice.lower(),
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
        "sample_email_1": sample_email_1,
        "sample_email_2": sample_email_2,
        "sample_email_3": sample_email_3,
    }
    new_members = [m.strip() for m in members_text.strip().split("\n") if m.strip()]

    with st.spinner("Saving..."):
        save_settings(new_settings)
        save_team_members(new_members)

    st.success("Settings saved. Refresh the app to apply changes.")
