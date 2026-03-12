import streamlit as st
import pandas as pd
from datetime import datetime
from sheets_db import load_leads
from lead_engine import calculate_priority

st.set_page_config(page_title="Catering AI", layout="wide", page_icon="🍗")

st.title("🍗 Chick-fil-A Catering — Sales Hub")

if st.button("🔄 Refresh", key="home_refresh"):
    load_leads.clear()
    st.rerun()

df = load_leads()

if df.empty:
    st.info("No leads yet. Go to **Find Leads** to get started.")
    st.stop()

# Always recalculate priority from source data
df["actual_revenue"] = pd.to_numeric(df["actual_revenue"], errors="coerce").fillna(0)
df["rating"] = pd.to_numeric(df["rating"], errors="coerce").fillna(0)
df["ratings_count"] = pd.to_numeric(df["ratings_count"], errors="coerce").fillna(0)
df["priority_score"] = df.apply(calculate_priority, axis=1)

# ── METRICS ────────────────────────────────────────────────────────────────────

total = len(df)
contacted = len(df[df["status"] != "Not Contacted"])
meetings = len(df[df["status"] == "Meeting Scheduled"])
proposals = len(df[df["status"] == "Proposal Sent"])
won = len(df[df["status"] == "Closed Won"])
lost = len(df[df["status"] == "Closed Lost"])
revenue = df["actual_revenue"].sum()
win_rate = round(won / (won + lost) * 100, 1) if (won + lost) > 0 else 0

def est_val(size):
    return {"large": 2000, "medium": 1000}.get(str(size).lower(), 500)

open_df = df[~df["status"].isin(["Closed Won", "Closed Lost"])].copy()
open_df["est_val"] = open_df["estimated_size"].apply(est_val)
pipeline_val = open_df["est_val"].sum()

c1, c2, c3, c4, c5, c6 = st.columns(6)
c1.metric("Total Leads", total)
c2.metric("Contacted", contacted)
c3.metric("Meetings", meetings)
c4.metric("Proposals", proposals)
c5.metric("Win Rate", f"{win_rate}%")
c6.metric("Revenue", f"${revenue:,.0f}")

st.markdown(f"**Open Pipeline Value:** ${pipeline_val:,.0f}")
st.markdown("---")

# ── ACTION PANELS ──────────────────────────────────────────────────────────────

today = datetime.today().strftime("%Y-%m-%d")
left, right = st.columns(2)

with left:
    st.subheader("🎯 Top Uncontacted Leads")
    top = df[df["status"] == "Not Contacted"].sort_values("priority_score", ascending=False).head(5)
    if top.empty:
        st.success("All leads contacted!")
    else:
        for _, row in top.iterrows():
            st.markdown(f"**{row['organization_name']}** — Score {row['priority_score']} | {row['category']}")

with right:
    st.subheader("📅 Follow-Ups Due Today")
    fu = df[df["next_follow_up_date"] == today]
    if fu.empty:
        st.success("No follow-ups due today.")
    else:
        for _, row in fu.iterrows():
            st.markdown(f"**{row['organization_name']}** — {row['status']} | {row['assigned_to'] or 'Unassigned'}")

st.markdown("---")

# ── PIPELINE CHART ─────────────────────────────────────────────────────────────

st.subheader("Pipeline by Stage")
stage = df["status"].value_counts().reset_index()
stage.columns = ["Stage", "Count"]
st.bar_chart(stage.set_index("Stage"))
