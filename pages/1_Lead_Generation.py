import streamlit as st
from lead_engine import generate_leads
from sheets_db import append_leads, load_leads, load_settings
from config import CATEGORY_OPTIONS

st.set_page_config(page_title="Lead Generation", layout="wide", page_icon="🔍")
st.title("🔍 Lead Generation")
st.caption("Pull real businesses from Google Places and add them to your pipeline.")

settings = load_settings()

# ── FORM ───────────────────────────────────────────────────────────────────────

with st.form("lead_form"):
    col1, col2, col3 = st.columns(3)
    zip_code = col1.text_input("ZIP Code", placeholder="e.g. 78201", value=settings.get("default_zip", ""))
    default_cat = settings.get("default_category", "school")
    cat_index = CATEGORY_OPTIONS.index(default_cat) if default_cat in CATEGORY_OPTIONS else 0
    category = col2.selectbox("Category", CATEGORY_OPTIONS, index=cat_index)
    radius = col3.slider("Radius (miles)", min_value=5, max_value=30, value=int(settings.get("default_radius", 10)))
    submitted = st.form_submit_button("🔍 Generate Leads", use_container_width=True)

if submitted:
    if not zip_code:
        st.error("Please enter a ZIP code.")
    else:
        with st.spinner(f"Searching for {category}s near {zip_code}..."):
            try:
                df = generate_leads(zip_code, category, radius)
                st.session_state["lead_results"] = df
                st.session_state["lead_added"] = False
            except Exception as e:
                st.error(f"Error: {e}")

# ── RESULTS ────────────────────────────────────────────────────────────────────

if "lead_results" in st.session_state:
    df = st.session_state["lead_results"]

    if df.empty:
        st.warning("No results found. Try a different ZIP code or category.")
    else:
        st.success(f"Found {len(df)} leads. Review below, then add to CRM.")

        st.dataframe(
            df[["organization_name", "address", "estimated_size", "rating", "ratings_count", "priority_score"]],
            use_container_width=True,
            hide_index=True,
        )

        st.markdown("---")

        if st.session_state.get("lead_added"):
            st.success("Leads already added to CRM.")
        else:
            if st.button("✅ Add All to CRM", use_container_width=True, type="primary"):
                with st.spinner("Saving to Google Sheets..."):
                    added = append_leads(df)
                if added == 0:
                    st.info("All leads already exist in the CRM (matched by Place ID).")
                else:
                    st.session_state["lead_added"] = True
                    load_leads.clear()
                    st.success(f"{added} new leads added to the CRM.")
                    st.balloons()

# ── CURRENT COUNT ──────────────────────────────────────────────────────────────

st.markdown("---")
existing = load_leads()
st.caption(f"Current CRM total: **{len(existing)} leads**")
