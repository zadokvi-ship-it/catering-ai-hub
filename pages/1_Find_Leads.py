import streamlit as st
from lead_engine import generate_leads
from sheets_db import append_leads, load_leads
from config import CATEGORY_OPTIONS
from sheets_db import load_settings

st.set_page_config(page_title="Find Leads", layout="wide", page_icon="🔍")
st.title("🔍 Find Leads")
st.caption("Search for real businesses via Google Places, review them, then add directly to your pipeline.")

settings = load_settings()

# ── SEARCH FORM ────────────────────────────────────────────────────────────────

with st.form("search_form"):
    c1, c2, c3 = st.columns(3)
    zip_code = c1.text_input("ZIP Code", value=settings.get("default_zip", ""), placeholder="e.g. 78201")
    default_cat = settings.get("default_category", "school")
    category = c2.selectbox("Category", CATEGORY_OPTIONS,
                             index=CATEGORY_OPTIONS.index(default_cat) if default_cat in CATEGORY_OPTIONS else 0)
    radius = c3.slider("Radius (miles)", 5, 30, int(settings.get("default_radius", 10)))
    search = st.form_submit_button("🔍 Search", use_container_width=True, type="primary")

if search:
    if not zip_code.strip():
        st.error("Enter a ZIP code.")
    else:
        with st.spinner("Pulling real businesses from Google Places..."):
            try:
                results = generate_leads(zip_code.strip(), category, radius)
                st.session_state["search_results"] = results
                st.session_state["search_added"] = False
            except Exception as e:
                st.error(f"Search failed: {e}")

# ── RESULTS ────────────────────────────────────────────────────────────────────

if "search_results" in st.session_state:
    df = st.session_state["search_results"]

    if df.empty:
        st.warning("No results found. Try adjusting the ZIP code or radius.")
    else:
        st.success(f"Found **{len(df)}** leads — review below, then add to your pipeline.")

        # Clean display table
        display = df[["organization_name", "address", "phone", "website",
                       "estimated_size", "rating", "priority_score"]].copy()
        display.columns = ["Organization", "Address", "Phone", "Website", "Size", "Rating", "Priority Score"]
        st.dataframe(display, use_container_width=True, hide_index=True)

        st.markdown("---")

        if st.session_state.get("search_added"):
            st.success("✅ Leads added to pipeline. Go to **Pipeline** to work them.")
        else:
            if st.button("➕ Add All to Pipeline", type="primary", use_container_width=True):
                with st.spinner("Saving to pipeline..."):
                    added = append_leads(df)
                if added == 0:
                    st.info("All these leads are already in your pipeline.")
                else:
                    st.session_state["search_added"] = True
                    load_leads.clear()
                    st.success(f"✅ {added} leads added. Go to **Pipeline** to work them.")
                    st.balloons()

st.markdown("---")
existing = load_leads()
st.caption(f"Pipeline total: **{len(existing)} leads**")
