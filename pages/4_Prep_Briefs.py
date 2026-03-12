import streamlit as st
import pandas as pd
from sheets_db import load_leads, load_settings
from research_engine import research_lead
from prep_engine import generate_prep_brief, generate_phone_script, generate_full_email

st.set_page_config(page_title="Prep Briefs", layout="wide", page_icon="📋")
st.title("📋 Prep Briefs & Scripts")
st.caption("Research the org, then generate a customized brief, phone script, and email — all tied to real events and real names.")

df = load_leads()
settings = load_settings()

if df.empty:
    st.info("No leads yet. Go to Lead Generation first.")
    st.stop()

brand_voice = settings.get("brand_voice", "")
sample_emails = [settings.get(f"sample_email_{i}", "") for i in range(1, 4)]
rep_settings = {
    "company_name": settings.get("company_name", "Chick-fil-A Catering"),
    "company_location": settings.get("company_location", ""),
    "rep_name": settings.get("rep_name", "[Your Name]"),
    "rep_title": settings.get("rep_title", "Catering Specialist"),
    "rep_email": settings.get("rep_email", "[Email]"),
    "rep_phone": settings.get("rep_phone", "[Phone]"),
}

df["priority_score"] = pd.to_numeric(df["priority_score"], errors="coerce").fillna(0)
df = df.sort_values("priority_score", ascending=False).reset_index(drop=True)

# ── SELECT LEAD ────────────────────────────────────────────────────────────────

lead_names = df["organization_name"].tolist()
selected_name = st.selectbox("Select a Lead", lead_names)
lead = df[df["organization_name"] == selected_name].iloc[0].to_dict()

col1, col2, col3, col4 = st.columns(4)
col1.markdown(f"**Category:** {lead['category']}")
col1.markdown(f"**Size:** {lead['estimated_size']}")
col2.markdown(f"**Decision Maker:** {lead['likely_decision_maker_role']}")
col2.markdown(f"**Phone:** {lead.get('phone') or '—'}")
col3.markdown(f"**Website:** {lead.get('website') or '—'}")
col3.markdown(f"**Address:** {lead.get('address') or '—'}")
col4.markdown(f"**Status:** {lead['status']}")
col4.markdown(f"**Priority Score:** {lead['priority_score']}")

st.markdown("---")

# ── STEP 1: RESEARCH ──────────────────────────────────────────────────────────

st.subheader("🔬 Step 1 — Research")
st.caption("Scrapes their website and extracts decision maker names, upcoming events, and the best angle to reach out.")

research_key = f"research_{selected_name}"

if st.button("🔬 Research This Organization", use_container_width=True, type="primary"):
    with st.spinner(f"Researching {selected_name}... scraping website and extracting intel..."):
        try:
            research = research_lead(lead)
            st.session_state[research_key] = research
        except Exception as e:
            st.error(f"Research failed: {e}")

if research_key in st.session_state:
    r = st.session_state[research_key]
    if r:
        rc1, rc2 = st.columns(2)
        with rc1:
            st.markdown(f"**Decision Maker:** {r.get('decision_maker_name', '—')}")
            if r.get("decision_maker_email"):
                st.markdown(f"**Email Found:** {r.get('decision_maker_email')}")
            st.markdown(f"**Best Contact Timing:** {r.get('best_contact_timing', '—')}")
            st.markdown(f"**Catering Angle:** {r.get('catering_angle', '—')}")
            st.markdown(f"**Personalization Hook:** {r.get('personalization_hook', '—')}")
        with rc2:
            if r.get("upcoming_events"):
                st.markdown("**Upcoming Events:**")
                for ev in r["upcoming_events"]:
                    st.markdown(f"- **{ev.get('event','')}** ({ev.get('date','')}) — {ev.get('catering_fit','')}")
            if r.get("org_notes"):
                st.markdown("**Key Notes:**")
                for note in r["org_notes"]:
                    st.markdown(f"- {note}")

st.markdown("---")

# ── STEP 2: GENERATE ──────────────────────────────────────────────────────────

st.subheader("⚡ Step 2 — Generate")

research = st.session_state.get(research_key, {})
if not research:
    st.info("Run the research step first for the best results. You can still generate without it.")

btn1, btn2, btn3 = st.columns(3)
gen_brief = btn1.button("📋 Full Prep Brief", use_container_width=True)
gen_phone = btn2.button("📞 Phone Script", use_container_width=True)
gen_email = btn3.button("✉️ Full Email", use_container_width=True)

if gen_brief:
    with st.spinner("Writing prep brief..."):
        try:
            brief = generate_prep_brief(lead, research=research, brand_voice=brand_voice,
                                        sample_emails=sample_emails, rep_settings=rep_settings)
            st.session_state[f"brief_{selected_name}"] = brief
        except Exception as e:
            st.error(f"Failed: {e}")

if gen_phone:
    with st.spinner("Writing phone script..."):
        try:
            script = generate_phone_script(lead, research=research, brand_voice=brand_voice,
                                           rep_settings=rep_settings)
            st.session_state[f"phone_{selected_name}"] = script
        except Exception as e:
            st.error(f"Failed: {e}")

if gen_email:
    with st.spinner("Writing full email..."):
        try:
            email = generate_full_email(lead, research=research, brand_voice=brand_voice,
                                        sample_emails=sample_emails, rep_settings=rep_settings)
            st.session_state[f"email_{selected_name}"] = email
        except Exception as e:
            st.error(f"Failed: {e}")

# ── OUTPUTS ────────────────────────────────────────────────────────────────────

brief_key = f"brief_{selected_name}"
phone_key = f"phone_{selected_name}"
email_key = f"email_{selected_name}"

if brief_key in st.session_state:
    st.markdown("---")
    st.subheader("📋 Prep Brief")
    st.markdown(st.session_state[brief_key])
    st.download_button("📥 Download Brief", data=st.session_state[brief_key],
                       file_name=f"brief_{selected_name.replace(' ','_')}.txt", mime="text/plain")

if phone_key in st.session_state:
    st.markdown("---")
    st.subheader("📞 Phone Script")
    st.markdown(st.session_state[phone_key])
    st.download_button("📥 Download Script", data=st.session_state[phone_key],
                       file_name=f"script_{selected_name.replace(' ','_')}.txt", mime="text/plain")

if email_key in st.session_state:
    st.markdown("---")
    st.subheader("✉️ Full Email")
    em = st.session_state[email_key]

    col_a, col_b = st.columns(2)
    col_a.markdown(f"**To:** {em.get('to_name', '')} `{em.get('to_email', '')}`")
    col_b.markdown(f"**Subject:** {em.get('subject', '')}")

    st.text_area("Complete Email (ready to send)", value=em.get("full_email", ""), height=350,
                 key="full_email_display")

    st.download_button("📥 Download Email", data=em.get("full_email", ""),
                       file_name=f"email_{selected_name.replace(' ','_')}.txt", mime="text/plain")

    # Option to send to approval queue
    if st.button("➕ Send to Email Approval Queue"):
        from sheets_db import append_email_draft
        from datetime import datetime
        record = {
            "place_id": lead["place_id"],
            "organization_name": lead["organization_name"],
            "to_name": em.get("to_name", ""),
            "to_email": em.get("to_email", ""),
            "subject": em.get("subject", ""),
            "body": em.get("full_email", ""),
            "status": "Pending Review",
            "drafted_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "reviewed_by": "", "reviewed_at": "", "notes": "",
        }
        append_email_draft(record)
        st.success("Added to Email Queue for review.")
