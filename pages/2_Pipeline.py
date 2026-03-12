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
st.title("📋 Pipeline")

# ── LOAD & PREP DATA ───────────────────────────────────────────────────────────

if st.button("🔄 Refresh", key="pipeline_refresh"):
    load_leads.clear()
    st.rerun()

try:
    df = load_leads()
except Exception as e:
    st.error(f"Could not load leads: {e}")
    st.stop()

if df.empty:
    st.info("No leads yet. Go to **Find Leads** to get started.")
    st.stop()

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

STATUS_ICONS = {
    "Not Contacted": "🔴",
    "Contacted": "🟡",
    "Meeting Scheduled": "🟠",
    "Proposal Sent": "🔵",
    "Closed Won": "🟢",
    "Closed Lost": "⚫",
}

# ── FILTERS ────────────────────────────────────────────────────────────────────

with st.expander("🔽 Filters", expanded=False):
    fc1, fc2, fc3 = st.columns(3)
    status_filter = fc1.multiselect("Status", PIPELINE_STATUSES, default=PIPELINE_STATUSES)
    cat_opts = df["category"].unique().tolist()
    cat_filter = fc2.multiselect("Category", cat_opts, default=cat_opts)
    rep_opts = ["All"] + [m for m in df["assigned_to"].unique().tolist() if m]
    rep_filter = fc3.multiselect("Assigned To", rep_opts, default=["All"])

filtered = df[df["status"].isin(status_filter) & df["category"].isin(cat_filter)]
if "All" not in rep_filter:
    filtered = filtered[filtered["assigned_to"].isin(rep_filter)]

# ── TWO-PANEL LAYOUT ───────────────────────────────────────────────────────────

list_col, detail_col = st.columns([2, 3], gap="large")

with list_col:
    st.markdown(f"**{len(filtered)} leads**")
    st.markdown("---")

    for _, row in filtered.iterrows():
        icon = STATUS_ICONS.get(row["status"], "⚪")
        is_selected = st.session_state.get("selected_lead") == row["place_id"]
        btn_type = "primary" if is_selected else "secondary"

        # Compact single-line label
        score = int(row["priority_score"])
        name = str(row["organization_name"])[:30]
        cat = str(row["category"])
        label = f"{icon} {name}  ·  {cat}  ·  {score}pts"

        if st.button(label, key=f"sel_{row['place_id']}", use_container_width=True, type=btn_type):
            st.session_state["selected_lead"] = row["place_id"]
            for k in list(st.session_state.keys()):
                if k.startswith(("research_", "brief_", "phone_", "email_gen_")):
                    del st.session_state[k]
            st.rerun()

# ── DETAIL PANEL ───────────────────────────────────────────────────────────────

with detail_col:
    selected_id = st.session_state.get("selected_lead")

    if not selected_id:
        st.markdown("### 👈 Select a lead to get started")
        st.caption("Click any lead on the left to view details, update status, research the org, and generate emails and scripts.")
        st.stop()

    lead_rows = df[df["place_id"] == selected_id]
    if lead_rows.empty:
        st.warning("Lead not found. It may have been deleted.")
        del st.session_state["selected_lead"]
        st.stop()

    lead = lead_rows.iloc[0].to_dict()

    # ── LEAD HEADER ────────────────────────────────────────────────────────────
    icon = STATUS_ICONS.get(lead["status"], "⚪")
    st.markdown(f"## {icon} {lead['organization_name']}")

    h1, h2, h3, h4 = st.columns(4)
    h1.metric("Priority Score", int(lead["priority_score"]))
    h2.metric("Status", lead["status"])
    h3.metric("Size", lead["estimated_size"].title())
    h4.metric("Category", lead["category"].title())

    st.markdown("---")

    # ── TABS ───────────────────────────────────────────────────────────────────
    tab_info, tab_update, tab_generate = st.tabs(["ℹ️ Info", "✏️ Update", "⚡ Generate"])

    # ── TAB 1: INFO ────────────────────────────────────────────────────────────
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

    # ── TAB 2: UPDATE ──────────────────────────────────────────────────────────
    with tab_update:
        with st.form(key=f"update_form_{lead['place_id']}"):
            u1, u2 = st.columns(2)
            new_status = u1.selectbox(
                "Status",
                PIPELINE_STATUSES,
                index=PIPELINE_STATUSES.index(lead["status"]) if lead["status"] in PIPELINE_STATUSES else 0,
            )
            assignee_opts = ["Unassigned"] + (team_members if team_members else [])
            current = lead.get("assigned_to") or "Unassigned"
            if current not in assignee_opts:
                assignee_opts.append(current)
            new_assignee = u2.selectbox(
                "Assigned To",
                assignee_opts,
                index=assignee_opts.index(current) if current in assignee_opts else 0,
            )

            new_followup = st.date_input(
                "Next Follow-Up Date",
                value=datetime.today() + timedelta(days=5),
                key=f"date_{lead['place_id']}",
            )
            new_notes = st.text_area(
                "Notes",
                value=str(lead.get("notes") or ""),
                key=f"notes_{lead['place_id']}",
            )
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
        if st.button("🗑️ Delete This Lead", key=f"del_{lead['place_id']}"):
            st.session_state[f"confirm_del_{lead['place_id']}"] = True

        if st.session_state.get(f"confirm_del_{lead['place_id']}"):
            st.warning("Delete this lead permanently?")
            d1, d2 = st.columns(2)
            if d1.button("Yes, delete", key=f"yes_del_{lead['place_id']}"):
                delete_lead(lead["place_id"])
                del st.session_state["selected_lead"]
                load_leads.clear()
                st.rerun()
            if d2.button("Cancel", key=f"no_del_{lead['place_id']}"):
                st.session_state[f"confirm_del_{lead['place_id']}"] = False
                st.rerun()

    # ── TAB 3: GENERATE ────────────────────────────────────────────────────────
    with tab_generate:
        research_key = f"research_{lead['place_id']}"
        brief_key = f"brief_{lead['place_id']}"
        phone_key = f"phone_{lead['place_id']}"
        email_key = f"email_gen_{lead['place_id']}"

        # Step 1: Research
        st.markdown("**Step 1 — Research the Organization**")
        if st.button("🔬 Research Now", key=f"res_btn_{lead['place_id']}", use_container_width=True):
            with st.spinner(f"Scraping {lead['organization_name']} and extracting intel..."):
                try:
                    st.session_state[research_key] = research_lead(lead)
                except Exception as e:
                    st.error(f"Research failed: {e}")

        research = st.session_state.get(research_key, {})
        if research:
            r1, r2 = st.columns(2)
            r1.markdown(f"**Decision Maker:** {research.get('decision_maker_name', '—')}")
            r1.markdown(f"**Best Angle:** {research.get('catering_angle', '—')}")
            r1.markdown(f"**Hook:** {research.get('personalization_hook', '—')}")
            if research.get("upcoming_events"):
                r2.markdown("**Upcoming Events:**")
                for ev in research["upcoming_events"]:
                    r2.markdown(f"- **{ev.get('event','')}** ({ev.get('date','')})")
        elif not research:
            st.caption("Research is optional but makes everything below much more specific and personalized.")

        st.markdown("---")

        # Step 2: Generate
        st.markdown("**Step 2 — Generate**")
        g1, g2, g3 = st.columns(3)

        if g1.button("📋 Prep Brief", key=f"brief_btn_{lead['place_id']}", use_container_width=True):
            with st.spinner("Writing brief..."):
                try:
                    st.session_state[brief_key] = generate_prep_brief(
                        lead, research=research, brand_voice=brand_voice,
                        sample_emails=sample_emails, rep_settings=rep_settings)
                except Exception as e:
                    st.error(f"Failed: {e}")

        if g2.button("📞 Phone Script", key=f"phone_btn_{lead['place_id']}", use_container_width=True):
            with st.spinner("Writing script..."):
                try:
                    st.session_state[phone_key] = generate_phone_script(
                        lead, research=research, brand_voice=brand_voice, rep_settings=rep_settings)
                except Exception as e:
                    st.error(f"Failed: {e}")

        if g3.button("✉️ Full Email", key=f"email_btn_{lead['place_id']}", use_container_width=True):
            with st.spinner("Writing email..."):
                try:
                    st.session_state[email_key] = generate_full_email(
                        lead, research=research, brand_voice=brand_voice,
                        sample_emails=sample_emails, rep_settings=rep_settings)
                except Exception as e:
                    st.error(f"Failed: {e}")

        # Output: Brief
        if brief_key in st.session_state:
            st.markdown("---")
            st.markdown("**📋 Prep Brief**")
            st.markdown(st.session_state[brief_key])
            st.download_button("📥 Download Brief", data=st.session_state[brief_key],
                               file_name=f"brief_{lead['organization_name'].replace(' ','_')}.txt",
                               mime="text/plain", key=f"dl_brief_{lead['place_id']}")

        # Output: Phone Script
        if phone_key in st.session_state:
            st.markdown("---")
            st.markdown("**📞 Phone Script**")
            st.markdown(st.session_state[phone_key])
            st.download_button("📥 Download Script", data=st.session_state[phone_key],
                               file_name=f"script_{lead['organization_name'].replace(' ','_')}.txt",
                               mime="text/plain", key=f"dl_phone_{lead['place_id']}")

        # Output: Email
        if email_key in st.session_state:
            st.markdown("---")
            em = st.session_state[email_key]
            st.markdown("**✉️ Full Email**")
            st.markdown(f"**To:** {em.get('to_name', '')} · **Subject:** {em.get('subject', '')}")
            st.text_area("Ready to send:", value=em.get("full_email", ""), height=300,
                         key=f"email_ta_{lead['place_id']}")

            ea, eb = st.columns(2)
            ea.download_button("📥 Download Email", data=em.get("full_email", ""),
                               file_name=f"email_{lead['organization_name'].replace(' ','_')}.txt",
                               mime="text/plain", key=f"dl_email_{lead['place_id']}")
            if eb.button("➕ Send to Approval Queue", key=f"queue_{lead['place_id']}"):
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
                st.success("Added to Email Queue.")
