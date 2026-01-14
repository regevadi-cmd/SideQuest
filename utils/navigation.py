"""Navigation utilities for SideQuest."""
import streamlit as st


def render_navigation(current_page: str = ""):
    """Render top navigation bar with page links."""
    pages = [
        ("🏠 Home", "app", "app.py"),
        ("🔍 Search", "search", "pages/1_search.py"),
        ("📋 Tracker", "tracker", "pages/2_tracker.py"),
        ("📄 Resume", "resume", "pages/3_resume.py"),
        ("👤 Profile", "profile", "pages/4_profile.py"),
        ("⚙️ Settings", "settings", "pages/5_settings.py"),
    ]

    # Header with branding and navigation
    col_brand, col_nav = st.columns([1, 4])

    with col_brand:
        st.markdown("""
        <div style="font-family: 'Plus Jakarta Sans', sans-serif; font-size: 1.5rem; font-weight: 800;
                    background: linear-gradient(135deg, #0891B2 0%, #22D3EE 100%);
                    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
                    padding: 0.5rem 0;">
            ⚔️ SideQuest
        </div>
        """, unsafe_allow_html=True)

    with col_nav:
        nav_cols = st.columns(len(pages))
        for i, (label, page_id, page_path) in enumerate(pages):
            with nav_cols[i]:
                is_current = page_id == current_page
                if is_current:
                    st.markdown(f"""
                    <div style="text-align: center; padding: 0.6rem 0.5rem;
                                background: rgba(8, 145, 178, 0.12); border-radius: 10px;
                                font-family: 'Plus Jakarta Sans', sans-serif;
                                font-size: 0.8rem; font-weight: 600; color: #0891B2;
                                white-space: nowrap;">
                        {label}
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.page_link(page_path, label=label, use_container_width=True)

    st.markdown("<hr style='margin: 0.5rem 0 1.5rem 0;'>", unsafe_allow_html=True)
