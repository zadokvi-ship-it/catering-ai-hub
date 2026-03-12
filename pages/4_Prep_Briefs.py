import streamlit as st
from sheets_db import load_leads
from prep_engine import generate_prep_brief
import pandas as pd

st.set_page_config(page_title="Prep Briefs", layout="wide", page_icon="📋")
st.title("📋 Prep Briefs")
st.caption("Generate a full call strategy, outreach email, objection handling, and follow-up timeline for any lead.")

df = load_leads()

if df.empty:
    st.info("No leads yet. Go to Lead Generation first.")
    st.stop()

df["priority_score"] = pd.to_numeric(df["priority_score"], errors="coerce").fillna(0)
df = df.sort_values("priority_score", ascending=False).reset_index(drop=True)

# ── SELECT LEAD ────────────────────────────────────────────────────────────────

lead_names = df["organization_name"].tolist()
selected_name = st.selectbox("Select a Lead", lead_names)

selected_lead = df[df["organization_name"] == selected_name].iloc[0].to_dict()

col1, col2, col3 = st.columns(3)
col1.markdown(f"**Category:** {selected_lead['category']}")
col1.markdown(f"**Size:** {selected_lead['estimated_size']}")
col2.markdown(f"**Decision Maker:** {selected_lead['likely_decision_maker_role']}")
col2.markdown(f"**Seasonal Opportunity:** {selected_lead['seasonal_opportunity']}")
col3.markdown(f"**Status:** {selected_lead['status']}")
col3.markdown(f"**Priority Score:** {selected_lead['priority_score']}")

st.markdown("---")

# ── GENERATE BRIEF ─────────────────────────────────────────────────────────────

if st.button("⚡ Generate Prep Brief", use_container_width=True):
    with st.spinner(f"Building strategy for {selected_name}..."):
        try:
            brief = generate_prep_brief(selected_lead)
            st.session_state[f"brief_{selected_name}"] = brief
        except Exception as e:
            st.error(f"Failed to generate brief: {e}")

# ── DISPLAY BRIEF ──────────────────────────────────────────────────────────────

brief_key = f"brief_{selected_name}"
if brief_key in st.session_state:
    st.markdown("---")
    st.subheader(f"Strategy Brief — {selected_name}")
    st.markdown(st.session_state[brief_key])

    st.download_button(
        label="📥 Download Brief as .txt",
        data=st.session_state[brief_key],
        file_name=f"brief_{selected_name.replace(' ', '_')}.txt",
        mime="text/plain",
    )
