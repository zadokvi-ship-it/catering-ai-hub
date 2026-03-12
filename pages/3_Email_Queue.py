import streamlit as st
from datetime import datetime
from sheets_db import load_email_queue, update_email_status, delete_email_draft

st.set_page_config(page_title="Email Queue", layout="wide", page_icon="✉️")
st.title("✉️ Email Queue")
st.caption("Review AI-drafted emails before they go out. Approve, edit, reject, or delete.")

if st.button("🔄 Refresh"):
    load_email_queue.clear()
    st.rerun()

df = load_email_queue()

if df.empty:
    st.info("No emails in the queue. Generate an email from any lead in the Pipeline.")
    st.stop()

STATUS_ICONS = {"Pending Review": "🟡", "Approved": "🟢", "Rejected": "🔴", "Sent": "✅"}

c1, c2 = st.columns([1, 3])
status_filter = c1.selectbox("Filter", ["All", "Pending Review", "Approved", "Rejected", "Sent"])

display_df = df if status_filter == "All" else df[df["status"] == status_filter]
st.markdown(f"**{len(display_df)} emails**")
st.markdown("---")

for i, row in display_df.iterrows():
    # Sheet row = dataframe index + 2 (1 for header, 1 for 0-based offset)
    sheet_row = i + 2
    icon = STATUS_ICONS.get(row["status"], "⚪")

    with st.expander(f"{icon} {row['organization_name']} — {row['status']} | {row['drafted_at']}"):

        c1, c2 = st.columns(2)
        to_name = c1.text_input("To Name", value=str(row.get("to_name", "")), key=f"to_name_{i}")
        to_email = c2.text_input("To Email", value=str(row.get("to_email", "")), key=f"to_email_{i}")
        subject = st.text_input("Subject", value=str(row.get("subject", "")), key=f"subj_{i}")
        body = st.text_area("Email Body", value=str(row.get("body", "")), height=280, key=f"body_{i}")
        reviewer = st.text_input("Your Name", key=f"reviewer_{i}", placeholder="Who is reviewing?")
        notes = st.text_area("Internal Notes", value=str(row.get("notes", "")),
                              height=60, key=f"notes_{i}")

        st.markdown("---")
        b1, b2, b3, b4, b5 = st.columns(5)

        if b1.button("✅ Approve", key=f"approve_{i}", use_container_width=True):
            update_email_status(row["place_id"], {
                "to_name": to_name, "to_email": to_email,
                "subject": subject, "body": body, "status": "Approved",
                "reviewed_by": reviewer,
                "reviewed_at": datetime.now().strftime("%Y-%m-%d %H:%M"), "notes": notes,
            })
            st.success("Approved.")
            st.rerun()

        if b2.button("❌ Reject", key=f"reject_{i}", use_container_width=True):
            update_email_status(row["place_id"], {
                "status": "Rejected", "reviewed_by": reviewer,
                "reviewed_at": datetime.now().strftime("%Y-%m-%d %H:%M"), "notes": notes,
            })
            st.rerun()

        if b3.button("📤 Mark Sent", key=f"sent_{i}", use_container_width=True):
            update_email_status(row["place_id"], {
                "status": "Sent", "reviewed_by": reviewer,
                "reviewed_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
            })
            st.rerun()

        if b4.button("💾 Save", key=f"save_{i}", use_container_width=True):
            update_email_status(row["place_id"], {
                "to_name": to_name, "to_email": to_email,
                "subject": subject, "body": body, "notes": notes,
            })
            st.success("Saved.")
            st.rerun()

        if b5.button("🗑️ Delete", key=f"delete_{i}", use_container_width=True):
            st.session_state[f"confirm_del_email_{i}"] = True

        if st.session_state.get(f"confirm_del_email_{i}"):
            st.warning("Delete this email permanently?")
            dc1, dc2 = st.columns(2)
            if dc1.button("Yes, delete", key=f"yes_del_email_{i}"):
                delete_email_draft(sheet_row)
                st.session_state.pop(f"confirm_del_email_{i}", None)
                st.rerun()
            if dc2.button("Cancel", key=f"no_del_email_{i}"):
                st.session_state.pop(f"confirm_del_email_{i}", None)
                st.rerun()
