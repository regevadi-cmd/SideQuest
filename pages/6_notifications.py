"""Notification Center Page - View and manage notifications."""
import streamlit as st
from datetime import datetime

from config import DB_PATH
from data.db_factory import Database
from styles import inject_styles, hero_section, section_header, empty_state
from utils.auth import require_auth, show_user_menu
from utils.navigation import render_navigation
from utils.sanitize import safe_html

# Page config
st.set_page_config(
    page_title="Notifications | SideQuest",
    page_icon="🔔",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Inject styles
inject_styles()

# Check authentication
if not require_auth():
    st.stop()

# Initialize database
if "db" not in st.session_state:
    st.session_state.db = Database(DB_PATH)

db = st.session_state.db

# Top navigation
render_navigation(current_page="notifications")

# Sidebar (minimal)
with st.sidebar:
    show_user_menu()

# Hero
st.markdown(hero_section(
    "🔔 Notification Center",
    "Stay updated on new jobs and application activity"
), unsafe_allow_html=True)

# Get notification counts
unread_count = db.get_unread_notification_count()
all_notifications = db.get_notifications(limit=50)

# Stats bar
st.markdown(f"""
<div style="display: flex; gap: 1rem; margin-bottom: 2rem;">
    <div style="flex: 1; background: rgba(8, 145, 178, 0.08); border: 1px solid rgba(8, 145, 178, 0.2);
                border-radius: 12px; padding: 1rem; text-align: center;">
        <div style="font-family: 'Plus Jakarta Sans', sans-serif; font-size: 2rem; font-weight: 700; color: #0891B2;">
            {unread_count}
        </div>
        <div style="font-size: 0.75rem; color: #94A3B8; text-transform: uppercase; font-weight: 600;">
            Unread
        </div>
    </div>
    <div style="flex: 1; background: #FFFFFF; border: 1px solid #E2E8F0;
                border-radius: 12px; padding: 1rem; text-align: center;">
        <div style="font-family: 'Plus Jakarta Sans', sans-serif; font-size: 2rem; font-weight: 700; color: #475569;">
            {len(all_notifications)}
        </div>
        <div style="font-size: 0.75rem; color: #94A3B8; text-transform: uppercase; font-weight: 600;">
            Total
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# Actions
col1, col2 = st.columns([3, 1])
with col2:
    if unread_count > 0:
        if st.button("Mark All Read", use_container_width=True):
            db.mark_all_notifications_read()
            st.rerun()

# Tabs for filtering
tab_unread, tab_all = st.tabs(["🔴 Unread", "📋 All"])

def render_notification(notif, key_prefix: str = ""):
    """Render a single notification card."""
    # Determine icon and color based on type
    type_config = {
        "new_jobs": {"icon": "💼", "color": "#0891B2", "bg": "rgba(8, 145, 178, 0.08)"},
        "application_update": {"icon": "📋", "color": "#10B981", "bg": "rgba(16, 185, 129, 0.08)"},
        "system": {"icon": "⚙️", "color": "#F59E0B", "bg": "rgba(245, 158, 11, 0.08)"}
    }
    config = type_config.get(notif.type, type_config["system"])

    # Time ago
    time_diff = datetime.now() - notif.created_at
    if time_diff.days > 0:
        time_ago = f"{time_diff.days}d ago"
    elif time_diff.seconds > 3600:
        time_ago = f"{time_diff.seconds // 3600}h ago"
    else:
        time_ago = f"{time_diff.seconds // 60}m ago"

    # Unread indicator
    unread_dot = """
    <div style="width: 8px; height: 8px; border-radius: 50%; background: #EF4444;"></div>
    """ if not notif.read else ""

    st.markdown(f"""
    <div style="background: {config['bg']}; border: 1px solid rgba({config['color']}, 0.2);
                border-radius: 12px; padding: 1rem; margin-bottom: 0.75rem;
                {'border-left: 4px solid ' + config['color'] if not notif.read else ''}">
        <div style="display: flex; align-items: flex-start; gap: 1rem;">
            <div style="font-size: 1.5rem;">{config['icon']}</div>
            <div style="flex: 1;">
                <div style="display: flex; align-items: center; gap: 0.5rem; margin-bottom: 0.25rem;">
                    {unread_dot}
                    <div style="font-family: 'Plus Jakarta Sans', sans-serif; font-weight: 700;
                                color: #0F172A; font-size: 1rem;">
                        {safe_html(notif.title)}
                    </div>
                </div>
                <div style="color: #475569; font-size: 0.875rem; line-height: 1.5;">
                    {safe_html(notif.message)}
                </div>
                <div style="color: #94A3B8; font-size: 0.75rem; margin-top: 0.5rem;">
                    {time_ago}
                </div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Action buttons
    col1, col2, col3 = st.columns([2, 1, 1])

    with col2:
        if not notif.read:
            if st.button("Mark Read", key=f"{key_prefix}read_{notif.id}", use_container_width=True):
                db.mark_notification_read(notif.id)
                st.rerun()

    with col3:
        if st.button("Delete", key=f"{key_prefix}del_{notif.id}", use_container_width=True):
            db.delete_notification(notif.id)
            st.toast("Notification deleted")
            st.rerun()

    # Show related jobs if any
    if notif.related_job_ids:
        with st.expander(f"View {len(notif.related_job_ids)} related job{'s' if len(notif.related_job_ids) > 1 else ''}"):
            for job_id in notif.related_job_ids[:5]:
                job = db.get_job(job_id)
                if job:
                    st.markdown(f"""
                    <div style="display: flex; align-items: center; gap: 1rem; padding: 0.75rem;
                                background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 8px; margin-bottom: 0.5rem;">
                        <div style="flex: 1;">
                            <div style="font-family: 'Plus Jakarta Sans', sans-serif; font-weight: 600; color: #0F172A;">
                                {safe_html(job.title)}
                            </div>
                            <div style="font-size: 0.875rem; color: #0891B2;">{safe_html(job.company)}</div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)


with tab_unread:
    unread_notifications = db.get_notifications(unread_only=True)

    if unread_notifications:
        for notif in unread_notifications:
            render_notification(notif, key_prefix="unread_")
    else:
        st.markdown(empty_state(
            "✨",
            "All caught up!",
            "You have no unread notifications."
        ), unsafe_allow_html=True)

with tab_all:
    if all_notifications:
        for notif in all_notifications:
            render_notification(notif, key_prefix="all_")

        # Clear all button
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🗑️ Clear All Notifications", type="secondary", use_container_width=True):
            db.clear_all_notifications()
            st.toast("All notifications cleared")
            st.rerun()
    else:
        st.markdown(empty_state(
            "🔔",
            "No notifications yet",
            "Notifications about new jobs and application updates will appear here."
        ), unsafe_allow_html=True)

# Settings link
st.markdown("<br>", unsafe_allow_html=True)
st.markdown("""
<div style="text-align: center; padding: 1rem;">
    <span style="color: #94A3B8; font-size: 0.875rem;">
        Configure auto-search and email notifications in
    </span>
</div>
""", unsafe_allow_html=True)

if st.button("⚙️ Notification Settings", use_container_width=True):
    st.switch_page("pages/5_settings.py")
