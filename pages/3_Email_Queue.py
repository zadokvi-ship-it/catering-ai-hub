import streamlit as st
from datetime import datetime
from sheets_db import load_email_queue, update_email_status

st.set_page_config(page_title="Email Queue", layout="wide", page_icon="✉️")
st.title("✉️ Email Approval Queue")
st.caption("Review AI-drafted emails. Approve to mark ready, then copy and send manually.")

if st.button("🔄 Refresh"):
    load_email_queue.clear()
    st.rerun()

df = load_email_queue()

if df.empty:
    st.info("No emails in the queue yet. Draft one from the CRM Pipeline page.")
    st.stop()

# ── FILTER BY STATUS ───────────────────────────────────────────────────────────

status_options = ["All", "Pending Review", "Approved", "Rejected", "Sent"]
status_filter = st.selectbox("Filter by Status", status_options)

if status_filter != "All":
    df = df[df["status"] == status_filter]

st.markdown(f"Showing **{len(df)}** emails")
st.markdown("---")

# ── EMAIL CARDS ────────────────────────────────────────────────────────────────

for i, row in df.iterrows():
    status_emoji = {
        "Pending Review": "🟡",
        "Approved": "🟢",
        "Rejected": "🔴",
        "Sent": "✅",
    }.get(row["status"], "⚪")

    with st.expander(f"{status_emoji} **{row['organization_name']}** — {row['status']} | Drafted: {row['drafted_at']}"):

        # ── RECIPIENT INFO ─────────────────────────────────────────────────────
        rc1, rc2 = st.columns(2)
        to_name = rc1.text_input("To Name", value=str(row["to_name"]), key=f"name_{row['place_id']}_{i}")
        to_email = rc2.text_input("To Email", value=str(row["to_email"]), key=f"email_{row['place_id']}_{i}")

        # ── EMAIL CONTENT ──────────────────────────────────────────────────────
        subject = st.text_input("Subject", value=str(row["subject"]), key=f"subj_{row['place_id']}_{i}")
        body = st.text_area("Email Body", value=str(row["body"]), height=300, key=f"body_{row['place_id']}_{i}")

        reviewer = st.text_input("Your Name (Reviewer)", key=f"rev_{row['place_id']}_{i}")
        notes = st.text_area("Internal Notes", value=str(row["notes"]), key=f"notes_{row['place_id']}_{i}")

        st.markdown("---")

        # ── ACTION BUTTONS ─────────────────────────────────────────────────────
        btn1, btn2, btn3, btn4 = st.columns(4)

        if btn1.button("✅ Approve", key=f"approve_{row['place_id']}_{i}"):
            update_email_status(row["place_id"], {
                "to_name": to_name,
                "to_email": to_email,
                "subject": subject,
                "body": body,
                "status": "Approved",
                "reviewed_by": reviewer,
                "reviewed_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "notes": notes,
            })
            st.success("Approved. Copy the email above and send it manually.")
            st.rerun()

        if btn2.button("❌ Reject", key=f"reject_{row['place_id']}_{i}"):
            update_email_status(row["place_id"], {
                "status": "Rejected",
                "reviewed_by": reviewer,
                "reviewed_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "notes": notes,
            })
            st.warning("Email rejected.")
            st.rerun()

        if btn3.button("📤 Mark as Sent", key=f"sent_{row['place_id']}_{i}"):
            update_email_status(row["place_id"], {
                "status": "Sent",
                "reviewed_by": reviewer,
                "reviewed_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "notes": notes,
            })
            st.success("Marked as sent.")
            st.rerun()

        if btn4.button("💾 Save Edits", key=f"save_{row['place_id']}_{i}"):
            update_email_status(row["place_id"], {
                "to_name": to_name,
                "to_email": to_email,
                "subject": subject,
                "body": body,
                "notes": notes,
            })
            st.success("Edits saved.")
            st.rerun()
