import streamlit as st
import pandas as pd
from sheets_db import load_leads, load_settings
from prep_engine import generate_prep_brief, generate_phone_script, generate_email_draft

st.set_page_config(page_title="Prep Briefs", layout="wide", page_icon="📋")
st.title("📋 Prep Briefs & Phone Scripts")
st.caption("Full outreach strategy, phone script, and email draft for any lead.")

df = load_leads()
settings = load_settings()

if df.empty:
    st.info("No leads yet. Go to Lead Generation first.")
    st.stop()

brand_voice = settings.get("brand_voice", "")
sample_emails = [settings.get(f"sample_email_{i}", "") for i in range(1, 4)]

df["priority_score"] = pd.to_numeric(df["priority_score"], errors="coerce").fillna(0)
df = df.sort_values("priority_score", ascending=False).reset_index(drop=True)

# ── SELECT LEAD ────────────────────────────────────────────────────────────────

lead_names = df["organization_name"].tolist()
selected_name = st.selectbox("Select a Lead", lead_names)
selected_lead = df[df["organization_name"] == selected_name].iloc[0].to_dict()

col1, col2, col3, col4 = st.columns(4)
col1.markdown(f"**Category:** {selected_lead['category']}")
col1.markdown(f"**Size:** {selected_lead['estimated_size']}")
col2.markdown(f"**Decision Maker:** {selected_lead['likely_decision_maker_role']}")
col2.markdown(f"**Phone:** {selected_lead.get('phone') or '—'}")
col3.markdown(f"**Seasonal Opportunity:** {selected_lead['seasonal_opportunity']}")
col3.markdown(f"**Website:** {selected_lead.get('website') or '—'}")
col4.markdown(f"**Status:** {selected_lead['status']}")
col4.markdown(f"**Priority Score:** {selected_lead['priority_score']}")

st.markdown("---")

# ── GENERATE BUTTONS ───────────────────────────────────────────────────────────

btn1, btn2, btn3 = st.columns(3)

gen_brief = btn1.button("📋 Generate Prep Brief", use_container_width=True, type="primary")
gen_phone = btn2.button("📞 Generate Phone Script", use_container_width=True, type="primary")
gen_email = btn3.button("✉️ Generate Email Draft", use_container_width=True, type="primary")

if gen_brief:
    with st.spinner(f"Building strategy for {selected_name}..."):
        try:
            brief = generate_prep_brief(selected_lead, brand_voice=brand_voice, sample_emails=sample_emails)
            st.session_state[f"brief_{selected_name}"] = brief
        except Exception as e:
            st.error(f"Failed: {e}")

if gen_phone:
    with st.spinner(f"Writing phone script for {selected_name}..."):
        try:
            script = generate_phone_script(selected_lead, brand_voice=brand_voice)
            st.session_state[f"phone_{selected_name}"] = script
        except Exception as e:
            st.error(f"Failed: {e}")

if gen_email:
    with st.spinner(f"Drafting email for {selected_name}..."):
        try:
            draft = generate_email_draft(selected_lead, brand_voice=brand_voice, sample_emails=sample_emails)
            st.session_state[f"email_preview_{selected_name}"] = draft
        except Exception as e:
            st.error(f"Failed: {e}")

# ── DISPLAY OUTPUTS ────────────────────────────────────────────────────────────

brief_key = f"brief_{selected_name}"
phone_key = f"phone_{selected_name}"
email_key = f"email_preview_{selected_name}"

if brief_key in st.session_state:
    st.markdown("---")
    st.subheader("📋 Prep Brief")
    st.markdown(st.session_state[brief_key])
    st.download_button(
        "📥 Download Brief",
        data=st.session_state[brief_key],
        file_name=f"brief_{selected_name.replace(' ', '_')}.txt",
        mime="text/plain",
    )

if phone_key in st.session_state:
    st.markdown("---")
    st.subheader("📞 Phone Script")
    st.markdown(st.session_state[phone_key])
    st.download_button(
        "📥 Download Phone Script",
        data=st.session_state[phone_key],
        file_name=f"phone_script_{selected_name.replace(' ', '_')}.txt",
        mime="text/plain",
    )

if email_key in st.session_state:
    st.markdown("---")
    st.subheader("✉️ Email Preview")
    draft = st.session_state[email_key]
    st.markdown(f"**Subject:** {draft.get('subject', '')}")
    st.text_area("Body", value=draft.get("body", ""), height=250, key="email_body_preview")
