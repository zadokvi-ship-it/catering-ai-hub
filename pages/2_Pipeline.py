import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from sheets_db import (load_leads, update_lead, delete_lead,
                        append_email_draft, load_team_members, load_settings)
from lead_engine import calculate_priority
from research_engine import research_lead
from prep_engine import generate_prep_brief, generate_phone_script, generate_full_email
from config import PIPELINE_STATUSES

st.set_page_config(page_title="Pipeline", layout="wide", page_icon="📋")

STATUS_ICONS = {
    "Not Contacted": "🔴",
    "Contacted": "🟡",
    "Meeting Scheduled": "🟠",
    "Proposal Sent": "🔵",
    "Closed Won": "🟢",
    "Closed Lost": "⚫",
}

# ── LOAD DATA ──────────────────────────────────────────────────────────────────

try:
    df = load_leads()
except Exception as e:
    st.error(f"Could not load leads: {e}")
    st.stop()

if not df.empty:
    df["actual_revenue"] = pd.to_numeric(df["actual_revenue"], errors="coerce").fillna(0)
    df["rating"] = pd.to_numeric(df["rating"], errors="coerce").fillna(0)
    df["ratings_count"] = pd.to_numeric(df["ratings_count"], errors="coerce").fillna(0)
    df["priority_score"] = df.apply(calculate_priority, axis=1)
    df = df.sort_values("priority_score", ascending=False).reset_index(drop=True)

settings = load_settings()
team_members = load_team_members()
brand_voice = settings.get("brand_voice", "")
sample_emails = [settings.get(f"sample_email_{i}", "") for i in range(1, 4)]
rep_settings = {k: settings.get(k, "") for k in
                ["company_name", "company_location", "rep_name", "rep_title", "rep_email", "rep_phone"]}
if not rep_settings["company_name"]:
    rep_settings["company_name"] = "Chick-fil-A Catering"

selected_id = st.session_state.get("selected_lead")

# ══════════════════════════════════════════════════════════════════════════════
# MODE 1 — LIST VIEW
# ══════════════════════════════════════════════════════════════════════════════

if not selected_id:
    st.title("📋 Pipeline")

    if st.button("🔄 Refresh", key="pipeline_refresh"):
        load_leads.clear()
        st.rerun()

    if df.empty:
        st.info("No leads yet. Go to **Find Leads** to get started.")
        st.stop()

    # Filters
    with st.expander("🔽 Filters", expanded=False):
        fc1, fc2 = st.columns(2)
        status_filter = fc1.multiselect("Status", PIPELINE_STATUSES, default=PIPELINE_STATUSES)
        cat_opts = df["category"].unique().tolist()
        cat_filter = fc2.multiselect("Category", cat_opts, default=cat_opts)

    filtered = df[df["status"].isin(status_filter) & df["category"].isin(cat_filter)]
    st.markdown(f"**{len(filtered)} leads**")
    st.markdown("---")

    for _, row in filtered.iterrows():
        icon = STATUS_ICONS.get(row["status"], "⚪")
        c1, c2, c3, c4 = st.columns([4, 2, 1, 1])
        c1.markdown(f"{icon} **{row['organization_name']}**")
        c2.markdown(f"{row['category'].title()} · {row['estimated_size'].title()}")
        c3.markdown(f"Score: **{int(row['priority_score'])}**")
        if c4.button("Open →", key=f"open_{row['place_id']}", use_container_width=True):
            st.session_state["selected_lead"] = row["place_id"]
            for k in list(st.session_state.keys()):
                if k.startswith(("research_", "brief_", "phone_", "email_gen_")):
                    del st.session_state[k]
            st.rerun()

    st.stop()

# ══════════════════════════════════════════════════════════════════════════════
# MODE 2 — FULL-SCREEN DETAIL VIEW
# ══════════════════════════════════════════════════════════════════════════════

if st.button("← Back to Pipeline"):
    del st.session_state["selected_lead"]
    st.rerun()

if df.empty or selected_id not in df["place_id"].values:
    st.warning("Lead not found.")
    del st.session_state["selected_lead"]
    st.rerun()

lead = df[df["place_id"] == selected_id].iloc[0].to_dict()

icon = STATUS_ICONS.get(lead["status"], "⚪")
st.title(f"{icon} {lead['organization_name']}")

h1, h2, h3, h4 = st.columns(4)
h1.metric("Priority Score", int(lead["priority_score"]))
h2.metric("Status", lead["status"])
h3.metric("Size", lead["estimated_size"].title())
h4.metric("Category", lead["category"].title())

st.markdown("---")

tab_info, tab_update, tab_generate = st.tabs(["ℹ️ Info", "✏️ Update Status", "⚡ Research & Generate"])

# ── TAB: INFO ─────────────────────────────────────────────────────────────────

with tab_info:
    i1, i2 = st.columns(2)
    i1.markdown(f"**Address:** {lead.get('address') or '—'}")
    i1.markdown(f"**Phone:** {lead.get('phone') or '—'}")
    i1.markdown(f"**Website:** {lead.get('website') or '—'}")
    i1.markdown(f"**Rating:** {lead.get('rating', '—')} ⭐ ({int(lead.get('ratings_count', 0))} reviews)")
    i2.markdown(f"**Decision Maker:** {lead.get('likely_decision_maker_role') or '—'}")
    i2.markdown(f"**Seasonal Opportunity:** {lead.get('seasonal_opportunity') or '—'}")
    i2.markdown(f"**Last Contact:** {lead.get('last_contact_date') or 'Never'}")
    i2.markdown(f"**Next Follow-Up:** {lead.get('next_follow_up_date') or '—'}")
    i2.markdown(f"**Assigned To:** {lead.get('assigned_to') or 'Unassigned'}")
    if lead.get("notes"):
        st.markdown(f"**Notes:** {lead['notes']}")

# ── TAB: UPDATE ───────────────────────────────────────────────────────────────

with tab_update:
    with st.form(key=f"update_{lead['place_id']}"):
        u1, u2 = st.columns(2)
        new_status = u1.selectbox(
            "Status",
            PIPELINE_STATUSES,
            index=PIPELINE_STATUSES.index(lead["status"]) if lead["status"] in PIPELINE_STATUSES else 0,
        )
        assignee_opts = ["Unassigned"] + (team_members or [])
        current = lead.get("assigned_to") or "Unassigned"
        if current not in assignee_opts:
            assignee_opts.append(current)
        new_assignee = u2.selectbox("Assigned To", assignee_opts,
                                     index=assignee_opts.index(current))
        new_followup = st.date_input("Next Follow-Up Date",
                                      value=datetime.today() + timedelta(days=5),
                                      key=f"date_{lead['place_id']}")
        new_notes = st.text_area("Notes", value=str(lead.get("notes") or ""),
                                  key=f"notes_{lead['place_id']}")
        new_revenue = None
        if new_status == "Closed Won":
            new_revenue = st.number_input("Revenue ($)", min_value=0.0, step=100.0,
                                           key=f"rev_{lead['place_id']}")
        saved = st.form_submit_button("💾 Save", type="primary", use_container_width=True)

    if saved:
        updates = {
            "status": new_status,
            "assigned_to": "" if new_assignee == "Unassigned" else new_assignee,
            "last_contact_date": datetime.today().strftime("%Y-%m-%d"),
            "notes": new_notes,
        }
        if new_status in ["Contacted", "Meeting Scheduled", "Proposal Sent"]:
            updates["next_follow_up_date"] = new_followup.strftime("%Y-%m-%d")
        if new_status in ["Closed Won", "Closed Lost"]:
            updates["next_follow_up_date"] = ""
        if new_revenue is not None:
            updates["actual_revenue"] = new_revenue
        with st.spinner("Saving..."):
            update_lead(lead["place_id"], updates)
        load_leads.clear()
        st.success("Saved.")
        st.rerun()

    st.markdown("---")
    if st.button("🗑️ Delete This Lead", key=f"del_btn_{lead['place_id']}"):
        st.session_state["confirm_delete"] = True

    if st.session_state.get("confirm_delete"):
        st.warning("Permanently delete this lead?")
        d1, d2 = st.columns(2)
        if d1.button("Yes, delete it", key="confirm_yes"):
            delete_lead(lead["place_id"])
            del st.session_state["selected_lead"]
            st.session_state.pop("confirm_delete", None)
            load_leads.clear()
            st.rerun()
        if d2.button("Cancel", key="confirm_no"):
            st.session_state.pop("confirm_delete", None)
            st.rerun()

# ── TAB: GENERATE ─────────────────────────────────────────────────────────────

with tab_generate:
    research_key = f"research_{lead['place_id']}"
    brief_key = f"brief_{lead['place_id']}"
    phone_key = f"phone_{lead['place_id']}"
    email_key = f"email_gen_{lead['place_id']}"

    # Step 1: Research
    st.markdown("### Step 1 — Research")
    st.caption("Scrapes their website and extracts decision maker names, upcoming events, and the best angle.")

    if st.button("🔬 Research This Organization", use_container_width=True,
                 key=f"res_{lead['place_id']}"):
        with st.spinner(f"Researching {lead['organization_name']}..."):
            try:
                st.session_state[research_key] = research_lead(lead)
            except Exception as e:
                st.error(f"Research failed: {e}")

    research = st.session_state.get(research_key, {})

    if research:
        r1, r2 = st.columns(2)
        with r1:
            st.markdown(f"**Decision Maker:** {research.get('decision_maker_name', '—')}")
            if research.get('decision_maker_email'):
                st.markdown(f"**Email Found:** {research.get('decision_maker_email')}")
            st.markdown(f"**Best Angle:** {research.get('catering_angle', '—')}")
            st.markdown(f"**Hook:** {research.get('personalization_hook', '—')}")
            st.markdown(f"**Best Time to Contact:** {research.get('best_contact_timing', '—')}")
        with r2:
            if research.get("upcoming_events"):
                st.markdown("**Upcoming Events:**")
                for ev in research["upcoming_events"]:
                    st.markdown(f"- **{ev.get('event','')}** ({ev.get('date','')})  \n  _{ev.get('catering_fit','')}_")
            if research.get("org_notes"):
                st.markdown("**Key Notes:**")
                for note in research["org_notes"]:
                    st.markdown(f"- {note}")
    else:
        st.caption("Optional but makes everything below much more specific.")

    st.markdown("---")
    st.markdown("### Step 2 — Generate")

    g1, g2, g3 = st.columns(3)
    gen_brief = g1.button("📋 Prep Brief", use_container_width=True, key=f"brief_btn_{lead['place_id']}")
    gen_phone = g2.button("📞 Phone Script", use_container_width=True, key=f"phone_btn_{lead['place_id']}")
    gen_email = g3.button("✉️ Full Email", use_container_width=True, key=f"email_btn_{lead['place_id']}")

    if gen_brief:
        with st.spinner("Writing prep brief..."):
            try:
                st.session_state[brief_key] = generate_prep_brief(
                    lead, research=research, brand_voice=brand_voice,
                    sample_emails=sample_emails, rep_settings=rep_settings)
            except Exception as e:
                st.error(f"Failed: {e}")

    if gen_phone:
        with st.spinner("Writing phone script..."):
            try:
                st.session_state[phone_key] = generate_phone_script(
                    lead, research=research, brand_voice=brand_voice, rep_settings=rep_settings)
            except Exception as e:
                st.error(f"Failed: {e}")

    if gen_email:
        with st.spinner("Writing email..."):
            try:
                st.session_state[email_key] = generate_full_email(
                    lead, research=research, brand_voice=brand_voice,
                    sample_emails=sample_emails, rep_settings=rep_settings)
            except Exception as e:
                st.error(f"Failed: {e}")

    # Show outputs full-width
    if brief_key in st.session_state:
        st.markdown("---")
        st.markdown("### 📋 Prep Brief")
        st.markdown(st.session_state[brief_key])
        st.download_button("📥 Download", data=st.session_state[brief_key],
                           file_name=f"brief_{lead['organization_name'].replace(' ','_')}.txt",
                           mime="text/plain", key=f"dl_brief_{lead['place_id']}")

    if phone_key in st.session_state:
        st.markdown("---")
        st.markdown("### 📞 Phone Script")
        st.markdown(st.session_state[phone_key])
        st.download_button("📥 Download", data=st.session_state[phone_key],
                           file_name=f"script_{lead['organization_name'].replace(' ','_')}.txt",
                           mime="text/plain", key=f"dl_phone_{lead['place_id']}")

    if email_key in st.session_state:
        st.markdown("---")
        em = st.session_state[email_key]
        st.markdown("### ✉️ Full Email")
        st.markdown(f"**To:** {em.get('to_name','—')}  ·  **Subject:** {em.get('subject','')}")
        st.text_area("Ready to copy & send:", value=em.get("full_email", ""),
                     height=320, key=f"email_ta_{lead['place_id']}")
        ea, eb = st.columns(2)
        ea.download_button("📥 Download", data=em.get("full_email", ""),
                           file_name=f"email_{lead['organization_name'].replace(' ','_')}.txt",
                           mime="text/plain", key=f"dl_email_{lead['place_id']}")
        if eb.button("➕ Send to Email Queue", key=f"queue_{lead['place_id']}"):
            append_email_draft({
                "place_id": lead["place_id"],
                "organization_name": lead["organization_name"],
                "to_name": em.get("to_name", ""),
                "to_email": em.get("to_email", ""),
                "subject": em.get("subject", ""),
                "body": em.get("full_email", ""),
                "status": "Pending Review",
                "drafted_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "reviewed_by": "", "reviewed_at": "", "notes": "",
            })
            st.success("Added to Email Queue.")
