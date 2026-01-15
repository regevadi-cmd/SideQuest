"""SideQuest - Student Job Search Agent."""
import streamlit as st
from pathlib import Path

from config import DB_PATH
from data.db_factory import Database
from styles import inject_styles, hero_section, stat_card, section_header, empty_state, feature_card
from utils.auth import require_auth, show_user_menu
from utils.navigation import render_navigation
from utils.settings import load_settings
from utils.sanitize import safe_html
from utils.auto_search import trigger_auto_search

# Page config must be first Streamlit command
st.set_page_config(
    page_title="SideQuest",
    page_icon="⚔️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Inject custom styles
inject_styles()

# Initialize database in session state
if "db" not in st.session_state:
    st.session_state.db = Database(DB_PATH)

# Load saved settings from database
load_settings(st.session_state.db)

# Trigger auto-search check (runs if due)
if "auto_search_checked" not in st.session_state:
    result = trigger_auto_search(st.session_state.db)
    if result and result.new_jobs > 0:
        st.toast(f"Auto-search found {result.new_jobs} new jobs!")
    st.session_state.auto_search_checked = True


def main():
    """Main application entry point."""

    # Check authentication first
    if not require_auth():
        return

    # Top navigation bar
    render_navigation(current_page="app")

    # User menu in sidebar (minimal)
    with st.sidebar:
        show_user_menu()

    # Hero section
    st.markdown(hero_section(
        "Welcome back! 👋",
        "Your personalized job search assistant is ready to help you land your dream role."
    ), unsafe_allow_html=True)

    # Get data
    db = st.session_state.db
    profile = db.get_profile()
    locations = db.get_locations()
    jobs = db.get_jobs(limit=1000)
    app_stats = db.get_application_stats()

    # Stats row
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        profile_status = "✓" if profile and profile.name else "—"
        st.markdown(stat_card(profile_status, "Profile"), unsafe_allow_html=True)

    with col2:
        st.markdown(stat_card(str(len(locations)), "Locations"), unsafe_allow_html=True)

    with col3:
        st.markdown(stat_card(str(len(jobs)), "Jobs Found", "coral"), unsafe_allow_html=True)

    with col4:
        total_apps = sum(app_stats.values())
        st.markdown(stat_card(str(total_apps), "Applications"), unsafe_allow_html=True)

    # Getting started section
    st.markdown(section_header("Quick Actions"), unsafe_allow_html=True)

    if not profile or not profile.name:
        st.markdown("""
        <div style="background: rgba(249, 115, 22, 0.08); border: 1px solid rgba(249, 115, 22, 0.2);
                    border-radius: 12px; padding: 1.25rem; margin-bottom: 1rem;">
            <div style="font-family: 'Plus Jakarta Sans', sans-serif; font-weight: 700; color: #F97316; margin-bottom: 0.5rem;">
                👤 Step 1: Set up your profile
            </div>
            <div style="color: #475569; font-size: 0.875rem;">
                Add your major, skills, and class schedule to get personalized job matches.
            </div>
        </div>
        """, unsafe_allow_html=True)

        if st.button("Set Up Profile →", type="primary"):
            st.switch_page("pages/4_profile.py")

    elif not locations:
        st.markdown("""
        <div style="background: rgba(8, 145, 178, 0.08); border: 1px solid rgba(8, 145, 178, 0.2);
                    border-radius: 12px; padding: 1.25rem; margin-bottom: 1rem;">
            <div style="font-family: 'Plus Jakarta Sans', sans-serif; font-weight: 700; color: #0891B2; margin-bottom: 0.5rem;">
                📍 Step 2: Add your location
            </div>
            <div style="color: #475569; font-size: 0.875rem;">
                Add your university or preferred search area to find nearby opportunities.
            </div>
        </div>
        """, unsafe_allow_html=True)

        if st.button("Add Location →", type="primary"):
            st.switch_page("pages/5_settings.py")

    else:
        # Ready to search
        col1, col2, col3 = st.columns(3)

        with col1:
            st.markdown(feature_card("🔍", "Search Jobs", "Find opportunities matching your profile"), unsafe_allow_html=True)
            if st.button("Start Searching", key="search_btn", use_container_width=True):
                st.switch_page("pages/1_search.py")

        with col2:
            st.markdown(feature_card("📋", "Track Applications", "Manage your job application pipeline"), unsafe_allow_html=True)
            if st.button("View Tracker", key="tracker_btn", use_container_width=True):
                st.switch_page("pages/2_tracker.py")

        with col3:
            st.markdown(feature_card("📝", "Resume Tools", "AI-powered cover letters & resume tips"), unsafe_allow_html=True)
            if st.button("Get Help", key="resume_btn", use_container_width=True):
                st.switch_page("pages/3_resume.py")

    # Recent activity
    st.markdown(section_header("Recent Activity"), unsafe_allow_html=True)

    recent_apps = db.get_applications()[:5]
    if recent_apps:
        for app in recent_apps:
            status_colors = {
                "Saved": "#6366F1",
                "Applied": "#0891B2",
                "Phone Screen": "#F59E0B",
                "Interview": "#F97316",
                "Offer": "#10B981",
                "Accepted": "#10B981",
                "Rejected": "#94A3B8",
                "Withdrawn": "#94A3B8"
            }
            color = status_colors.get(app.status, "#6366F1")

            st.markdown(f"""
            <div style="display: flex; align-items: center; gap: 1rem; padding: 1rem;
                        background: #FFFFFF; border: 1px solid #E2E8F0;
                        border-radius: 12px; margin-bottom: 0.75rem;">
                <div style="width: 8px; height: 8px; border-radius: 50%; background: {color};"></div>
                <div style="flex: 1;">
                    <div style="font-family: 'Plus Jakarta Sans', sans-serif; font-weight: 600; color: #0F172A;">
                        {safe_html(app.job.title)}
                    </div>
                    <div style="font-size: 0.875rem; color: #475569;">
                        {safe_html(app.job.company)}
                    </div>
                </div>
                <div style="font-family: 'Nunito Sans', sans-serif; font-size: 0.75rem;
                            padding: 0.35rem 0.75rem; background: rgba(99, 102, 241, 0.1);
                            border-radius: 20px; color: {color}; font-weight: 600;">
                    {safe_html(app.status)}
                </div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.markdown(empty_state(
            "📭",
            "No activity yet",
            "Start by searching for jobs and saving the ones you're interested in."
        ), unsafe_allow_html=True)

    # Footer
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; padding: 1rem; color: #94A3B8; font-size: 0.75rem;">
        <span style="font-family: 'Plus Jakarta Sans', sans-serif; font-weight: 700;">⚔️ SideQuest</span>
        · Student Job Search Agent · Powered by AI
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
