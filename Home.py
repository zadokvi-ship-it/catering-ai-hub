import streamlit as st
import pandas as pd
from sheets_db import load_leads
from config import PIPELINE_STATUSES

st.set_page_config(page_title="Catering AI Hub", layout="wide", page_icon="🍽️")

st.title("🍽️ Catering AI — Command Hub")
st.caption("Use the sidebar to navigate between modules.")

# ── LOAD DATA ──────────────────────────────────────────────────────────────────

if st.button("🔄 Refresh Data"):
    load_leads.clear()
    st.rerun()

df = load_leads()

if df.empty:
    st.info("No leads yet. Go to **Lead Generation** to pull your first batch.")
    st.stop()

df["actual_revenue"] = pd.to_numeric(df["actual_revenue"], errors="coerce").fillna(0)
df["priority_score"] = pd.to_numeric(df["priority_score"], errors="coerce").fillna(0)

# ── METRICS ────────────────────────────────────────────────────────────────────

total = len(df)
contacted = len(df[df["status"] != "Not Contacted"])
meetings = len(df[df["status"] == "Meeting Scheduled"])
proposals = len(df[df["status"] == "Proposal Sent"])
closed_won = len(df[df["status"] == "Closed Won"])
closed_lost = len(df[df["status"] == "Closed Lost"])
total_revenue = df["actual_revenue"].sum()

win_rate = 0
if (closed_won + closed_lost) > 0:
    win_rate = round((closed_won / (closed_won + closed_lost)) * 100, 1)

open_pipeline = df[df["status"].isin(["Not Contacted", "Contacted", "Meeting Scheduled", "Proposal Sent"])]

def pipeline_value(size):
    size = str(size).lower()
    if size == "large":
        return 2000
    elif size == "medium":
        return 1000
    return 500

open_pipeline = open_pipeline.copy()
open_pipeline["est_value"] = open_pipeline["estimated_size"].apply(pipeline_value)
pipeline_total = open_pipeline["est_value"].sum()
projected = round(pipeline_total * (win_rate / 100), 2) if win_rate > 0 else 0

# ── TOP ROW ────────────────────────────────────────────────────────────────────

col1, col2, col3, col4, col5, col6 = st.columns(6)
col1.metric("Total Leads", total)
col2.metric("Contacted", contacted)
col3.metric("Meetings", meetings)
col4.metric("Proposals", proposals)
col5.metric("Win Rate", f"{win_rate}%")
col6.metric("Revenue Closed", f"${total_revenue:,.0f}")

st.markdown("---")

col7, col8 = st.columns(2)
col7.metric("Open Pipeline Value", f"${pipeline_total:,.0f}")
col8.metric("Projected Revenue", f"${projected:,.0f}")

st.markdown("---")

# ── FUNNEL ─────────────────────────────────────────────────────────────────────

left, right = st.columns(2)

with left:
    st.subheader("📈 Pipeline Funnel")
    funnel = pd.DataFrame({
        "Stage": ["Total Leads", "Contacted", "Meetings", "Proposals", "Closed Won"],
        "Count": [total, contacted, meetings, proposals, closed_won],
    })
    st.bar_chart(funnel.set_index("Stage"))

with right:
    st.subheader("🗂 Leads by Status")
    status_counts = df["status"].value_counts().reset_index()
    status_counts.columns = ["Status", "Count"]
    st.bar_chart(status_counts.set_index("Status"))

st.markdown("---")

# ── TODAY'S ACTION PANEL ───────────────────────────────────────────────────────

st.subheader("🔥 Today's Action Panel")

from datetime import datetime
today = datetime.today().strftime("%Y-%m-%d")

colA, colB = st.columns(2)

with colA:
    st.markdown("### 🎯 Top Priority Targets")
    top = df[df["status"] == "Not Contacted"].sort_values("priority_score", ascending=False).head(5)
    if top.empty:
        st.success("All leads contacted.")
    else:
        st.dataframe(
            top[["organization_name", "category", "estimated_size", "priority_score"]],
            use_container_width=True,
            hide_index=True,
        )

with colB:
    st.markdown("### 📅 Follow-Ups Due Today")
    followups = df[df["next_follow_up_date"] == today]
    if followups.empty:
        st.success("No follow-ups due today.")
    else:
        st.dataframe(
            followups[["organization_name", "status", "assigned_to"]],
            use_container_width=True,
            hide_index=True,
        )
