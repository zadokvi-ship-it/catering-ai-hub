import streamlit as st
import pandas as pd
from lead_engine import generate_leads
from sheets_db import append_leads, load_leads, load_settings
from config import CATEGORY_OPTIONS

st.set_page_config(page_title="Find Leads", layout="wide", page_icon="🔍")
st.title("🔍 Find Leads")
st.caption("Search for real businesses, select the ones you want, then add them to your pipeline.")

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
                st.session_state["selected_leads"] = []
            except Exception as e:
                st.error(f"Search failed: {e}")

# ── RESULTS WITH CHECKBOXES ────────────────────────────────────────────────────

if "search_results" in st.session_state:
    df = st.session_state["search_results"]

    if df.empty:
        st.warning("No results found. Try adjusting the ZIP code or radius.")
    else:
        st.success(f"Found **{len(df)}** leads — check the ones you want, then add to pipeline.")
        st.markdown("---")

        # Add a Select column for checkboxes
        display_df = df[["organization_name", "address", "phone", "website",
                          "estimated_size", "rating", "priority_score"]].copy()
        display_df.insert(0, "Add?", True)
        display_df.columns = ["Add?", "Organization", "Address", "Phone",
                               "Website", "Size", "Rating", "Priority"]

        edited = st.data_editor(
            display_df,
            column_config={
                "Add?": st.column_config.CheckboxColumn("Add?", default=True, width="small"),
                "Organization": st.column_config.TextColumn("Organization", width="large"),
                "Address": st.column_config.TextColumn("Address", width="large"),
                "Phone": st.column_config.TextColumn("Phone", width="medium"),
                "Website": st.column_config.LinkColumn("Website", width="medium"),
                "Size": st.column_config.TextColumn("Size", width="small"),
                "Rating": st.column_config.NumberColumn("Rating", width="small"),
                "Priority": st.column_config.NumberColumn("Priority", width="small"),
            },
            hide_index=True,
            use_container_width=True,
            key="lead_selector",
        )

        selected_count = edited["Add?"].sum()
        st.caption(f"**{selected_count}** of {len(df)} leads selected")

        st.markdown("---")

        if st.session_state.get("search_added"):
            st.success("✅ Leads added. Go to **Pipeline** to work them.")
        else:
            col_a, col_b = st.columns([1, 3])
            if col_a.button("➕ Add Selected to Pipeline", type="primary", use_container_width=True,
                            disabled=(selected_count == 0)):
                selected_indices = edited[edited["Add?"]].index.tolist()
                to_add = df.iloc[selected_indices]
                with st.spinner(f"Adding {len(to_add)} leads to pipeline..."):
                    added = append_leads(to_add)
                if added == 0:
                    st.info("All selected leads are already in your pipeline.")
                else:
                    st.session_state["search_added"] = True
                    load_leads.clear()
                    st.success(f"✅ {added} leads added. Go to **Pipeline** to work them.")
                    st.balloons()

st.markdown("---")
existing = load_leads()
st.caption(f"Pipeline total: **{len(existing)} leads**")
