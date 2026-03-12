import streamlit as st
import pandas as pd
from sheets_db import load_leads

st.set_page_config(page_title="Analytics", layout="wide", page_icon="📊")
st.title("📊 Analytics")

if st.button("🔄 Refresh"):
    load_leads.clear()
    st.rerun()

df = load_leads()

if df.empty:
    st.info("No data yet. Generate and work some leads first.")
    st.stop()

df["actual_revenue"] = pd.to_numeric(df["actual_revenue"], errors="coerce").fillna(0)
df["priority_score"] = pd.to_numeric(df["priority_score"], errors="coerce").fillna(0)
df["rating"] = pd.to_numeric(df["rating"], errors="coerce").fillna(0)

closed_won = df[df["status"] == "Closed Won"]
closed_lost = df[df["status"] == "Closed Lost"]
open_leads = df[~df["status"].isin(["Closed Won", "Closed Lost"])]

def est_value(size):
    size = str(size).lower()
    if size == "large": return 2000
    if size == "medium": return 1000
    return 500

open_leads = open_leads.copy()
open_leads["est_value"] = open_leads["estimated_size"].apply(est_value)

# ── TOP METRICS ────────────────────────────────────────────────────────────────

total = len(df)
won = len(closed_won)
lost = len(closed_lost)
win_rate = round((won / (won + lost)) * 100, 1) if (won + lost) > 0 else 0
total_revenue = closed_won["actual_revenue"].sum()
avg_deal = round(total_revenue / won, 2) if won > 0 else 0
pipeline_value = open_leads["est_value"].sum()

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Total Leads", total)
c2.metric("Win Rate", f"{win_rate}%")
c3.metric("Revenue Closed", f"${total_revenue:,.0f}")
c4.metric("Avg Deal Size", f"${avg_deal:,.0f}")
c5.metric("Open Pipeline", f"${pipeline_value:,.0f}")

st.markdown("---")

# ── ROW 1: CONVERSION + REVENUE BY CATEGORY ───────────────────────────────────

row1_left, row1_right = st.columns(2)

with row1_left:
    st.subheader("Conversion Rate by Category")
    categories = df["category"].unique()
    conv_data = []
    for cat in categories:
        cat_df = df[df["category"] == cat]
        cat_won = len(cat_df[cat_df["status"] == "Closed Won"])
        cat_lost = len(cat_df[cat_df["status"] == "Closed Lost"])
        rate = round((cat_won / (cat_won + cat_lost)) * 100, 1) if (cat_won + cat_lost) > 0 else 0
        conv_data.append({"Category": cat, "Win Rate %": rate})
    conv_df = pd.DataFrame(conv_data).set_index("Category")
    st.bar_chart(conv_df)

with row1_right:
    st.subheader("Revenue Closed by Category")
    if not closed_won.empty:
        rev_by_cat = closed_won.groupby("category")["actual_revenue"].sum().reset_index()
        rev_by_cat.columns = ["Category", "Revenue"]
        st.bar_chart(rev_by_cat.set_index("Category"))
    else:
        st.info("No closed deals yet.")

st.markdown("---")

# ── ROW 2: REP LEADERBOARD + PIPELINE BY STAGE ────────────────────────────────

row2_left, row2_right = st.columns(2)

with row2_left:
    st.subheader("Rep Leaderboard")
    if df["assigned_to"].str.strip().eq("").all():
        st.info("No leads assigned yet. Assign leads in the CRM Pipeline.")
    else:
        reps = df[df["assigned_to"].str.strip() != ""]
        leaderboard = reps.groupby("assigned_to").agg(
            Leads=("organization_name", "count"),
            Closed_Won=("status", lambda x: (x == "Closed Won").sum()),
            Revenue=("actual_revenue", "sum"),
        ).reset_index()
        leaderboard.columns = ["Rep", "Leads", "Closed Won", "Revenue ($)"]
        leaderboard = leaderboard.sort_values("Revenue ($)", ascending=False)
        st.dataframe(leaderboard, use_container_width=True, hide_index=True)

with row2_right:
    st.subheader("Pipeline by Stage")
    stage_counts = df["status"].value_counts().reset_index()
    stage_counts.columns = ["Stage", "Count"]
    st.bar_chart(stage_counts.set_index("Stage"))

st.markdown("---")

# ── ROW 3: LEAD QUALITY + SIZE BREAKDOWN ──────────────────────────────────────

row3_left, row3_right = st.columns(2)

with row3_left:
    st.subheader("Leads by Size")
    size_counts = df["estimated_size"].value_counts().reset_index()
    size_counts.columns = ["Size", "Count"]
    st.bar_chart(size_counts.set_index("Size"))

with row3_right:
    st.subheader("Priority Score Distribution")
    score_df = df[["organization_name", "priority_score"]].sort_values("priority_score", ascending=False).head(20)
    st.bar_chart(score_df.set_index("organization_name"))

st.markdown("---")

# ── FULL DATA TABLE ────────────────────────────────────────────────────────────

st.subheader("Full Lead Table")
display_cols = ["organization_name", "category", "status", "assigned_to",
                "priority_score", "estimated_size", "actual_revenue", "next_follow_up_date"]
st.dataframe(
    df[display_cols].sort_values("priority_score", ascending=False),
    use_container_width=True,
    hide_index=True,
)
