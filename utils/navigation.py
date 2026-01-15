"""Navigation utilities for SideQuest."""
import streamlit as st
from config import DB_PATH


def get_unread_count() -> int:
    """Get unread notification count for badge display."""
    try:
        from data.db_factory import Database
        if "db" not in st.session_state:
            st.session_state.db = Database(DB_PATH)
        return st.session_state.db.get_unread_notification_count()
    except Exception:
        return 0


def render_navigation(current_page: str = ""):
    """Render top navigation bar with page links."""
    # Get unread count for notification badge
    unread_count = get_unread_count()
    notif_label = f"🔔 ({unread_count})" if unread_count > 0 else "🔔"

    pages = [
        ("🏠 Home", "app", "app.py"),
        ("🔍 Search", "search", "pages/1_search.py"),
        ("📋 Tracker", "tracker", "pages/2_tracker.py"),
        ("📄 Resume", "resume", "pages/3_resume.py"),
        ("👤 Profile", "profile", "pages/4_profile.py"),
        (notif_label, "notifications", "pages/6_notifications.py"),
        ("⚙️", "settings", "pages/5_settings.py"),
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
                    # Add red badge for unread notifications
                    badge_style = ""
                    if page_id == "notifications" and unread_count > 0:
                        badge_style = "border: 2px solid #EF4444;"

                    st.markdown(f"""
                    <div style="text-align: center; padding: 0.6rem 0.5rem;
                                background: rgba(8, 145, 178, 0.12); border-radius: 10px;
                                font-family: 'Plus Jakarta Sans', sans-serif;
                                font-size: 0.8rem; font-weight: 600; color: #0891B2;
                                white-space: nowrap; {badge_style}">
                        {label}
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.page_link(page_path, label=label, use_container_width=True)

    st.markdown("<hr style='margin: 0.5rem 0 1.5rem 0;'>", unsafe_allow_html=True)
