import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from sheets_db import load_leads, update_lead, append_email_draft
from prep_engine import generate_email_draft
from config import PIPELINE_STATUSES

st.set_page_config(page_title="CRM Pipeline", layout="wide", page_icon="🗂")
st.title("🗂 CRM Pipeline")

if st.button("🔄 Refresh"):
    load_leads.clear()
    st.rerun()

df = load_leads()

if df.empty:
    st.info("No leads yet. Go to Lead Generation first.")
    st.stop()

df["priority_score"] = pd.to_numeric(df["priority_score"], errors="coerce").fillna(0)
df["actual_revenue"] = pd.to_numeric(df["actual_revenue"], errors="coerce").fillna(0)

# ── FILTERS ────────────────────────────────────────────────────────────────────

col1, col2, col3 = st.columns(3)
status_filter = col1.multiselect("Filter by Status", PIPELINE_STATUSES, default=PIPELINE_STATUSES)
category_filter = col2.multiselect("Filter by Category", df["category"].unique().tolist(), default=df["category"].unique().tolist())
assignee_filter = col3.multiselect("Filter by Assigned To", ["All"] + df["assigned_to"].unique().tolist(), default=["All"])

filtered = df[df["status"].isin(status_filter) & df["category"].isin(category_filter)]
if "All" not in assignee_filter:
    filtered = filtered[filtered["assigned_to"].isin(assignee_filter)]

filtered = filtered.sort_values("priority_score", ascending=False).reset_index(drop=True)

st.markdown(f"Showing **{len(filtered)}** leads")
st.markdown("---")

# ── LEAD CARDS ─────────────────────────────────────────────────────────────────

for i, row in filtered.iterrows():
    with st.expander(f"**{row['organization_name']}** — {row['status']} | Score: {row['priority_score']}"):
        col_a, col_b, col_c = st.columns(3)
        col_a.markdown(f"**Category:** {row['category']}")
        col_a.markdown(f"**Size:** {row['estimated_size']}")
        col_a.markdown(f"**Address:** {row['address']}")
        col_b.markdown(f"**Decision Maker:** {row['likely_decision_maker_role']}")
        col_b.markdown(f"**Seasonal Opportunity:** {row['seasonal_opportunity']}")
        col_b.markdown(f"**Rating:** {row['rating']} ⭐ ({row['ratings_count']} reviews)")
        col_c.markdown(f"**Last Contact:** {row['last_contact_date'] or 'Never'}")
        col_c.markdown(f"**Next Follow-Up:** {row['next_follow_up_date'] or '—'}")
        col_c.markdown(f"**Assigned To:** {row['assigned_to'] or 'Unassigned'}")

        if row["notes"]:
            st.markdown(f"**Notes:** {row['notes']}")

        st.markdown("---")

        # ── UPDATE FORM ────────────────────────────────────────────────────────
        with st.form(key=f"update_{row['place_id']}"):
            uc1, uc2, uc3 = st.columns(3)
            new_status = uc1.selectbox(
                "Update Status",
                PIPELINE_STATUSES,
                index=PIPELINE_STATUSES.index(row["status"]) if row["status"] in PIPELINE_STATUSES else 0,
            )
            new_assignee = uc2.text_input("Assigned To", value=str(row["assigned_to"]))
            new_followup = uc3.date_input(
                "Next Follow-Up",
                value=datetime.today() + timedelta(days=5),
            )
            new_notes = st.text_area("Notes", value=str(row["notes"]))
            new_revenue = None
            if new_status == "Closed Won":
                new_revenue = st.number_input("Revenue Amount ($)", min_value=0.0, step=100.0)

            save_btn = st.form_submit_button("💾 Save Update")

        if save_btn:
            updates = {
                "status": new_status,
                "assigned_to": new_assignee,
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
                update_lead(row["place_id"], updates)
            st.success("Lead updated.")
            st.rerun()

        # ── DRAFT EMAIL BUTTON ─────────────────────────────────────────────────
        if st.button("✉️ Draft Outreach Email", key=f"email_{row['place_id']}"):
            with st.spinner("Generating email draft..."):
                try:
                    draft = generate_email_draft(row.to_dict())
                    from datetime import datetime as dt
                    email_record = {
                        "place_id": row["place_id"],
                        "organization_name": row["organization_name"],
                        "to_name": "",
                        "to_email": "",
                        "subject": draft.get("subject", ""),
                        "body": draft.get("body", ""),
                        "status": "Pending Review",
                        "drafted_at": dt.now().strftime("%Y-%m-%d %H:%M"),
                        "reviewed_by": "",
                        "reviewed_at": "",
                        "notes": "",
                    }
                    append_email_draft(email_record)
                    st.success("Draft added to Email Queue. Review it in the Email Queue page.")
                except Exception as e:
                    st.error(f"Failed to generate draft: {e}")
