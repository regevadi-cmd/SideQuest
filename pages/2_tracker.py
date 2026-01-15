"""Application Tracker Page - Track job applications and their status."""
import streamlit as st
from datetime import date

from config import DB_PATH, APPLICATION_STATUSES
from data.db_factory import Database
from data.models import Application
from styles import inject_styles, hero_section, section_header, empty_state, pipeline_stage
from utils.auth import require_auth, show_user_menu
from utils.navigation import render_navigation
from utils.sanitize import safe_html, safe_url

# Page config
st.set_page_config(
    page_title="Application Tracker | SideQuest",
    page_icon="📋",
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
render_navigation(current_page="tracker")

# Sidebar (minimal)
with st.sidebar:
    show_user_menu()

# Hero
st.markdown(hero_section(
    "📋 Application Tracker",
    "Monitor your job applications and stay on top of your search"
), unsafe_allow_html=True)

# Get statistics
stats = db.get_application_stats()
total = sum(stats.values())

# Visual pipeline
st.markdown(section_header("Your Pipeline"), unsafe_allow_html=True)

# Pipeline stages with visual flow
stage_config = [
    ("Saved", "📌", "#6366F1"),
    ("Applied", "📤", "#0891B2"),
    ("Phone Screen", "📞", "#F59E0B"),
    ("Interview", "🎤", "#F97316"),
    ("Offer", "🎉", "#10B981"),
]

# Build pipeline stages
stage_cards = []
for status, emoji, color in stage_config:
    count = stats.get(status, 0)
    is_active = count > 0
    bg_color = "rgba(8, 145, 178, 0.08)" if is_active else "#FFFFFF"
    border_color = color if is_active else "#E2E8F0"

    stage_cards.append(f'''<div style="flex: 1; min-width: 120px; background: {bg_color}; border: 1px solid {border_color}; border-radius: 16px; padding: 1.25rem; text-align: center; transition: all 0.2s ease;"><div style="font-size: 1.5rem; margin-bottom: 0.5rem;">{emoji}</div><div style="font-family: 'Plus Jakarta Sans', sans-serif; font-size: 1.75rem; font-weight: 700; color: {color};">{count}</div><div style="font-family: 'Nunito Sans', sans-serif; font-size: 0.7rem; color: #94A3B8; text-transform: uppercase; letter-spacing: 0.05em;">{status}</div></div>''')

# Add outcomes (Accepted/Rejected)
accepted = stats.get("Accepted", 0)
rejected = stats.get("Rejected", 0)

outcomes_html = f'''<div style="min-width: 100px; display: flex; flex-direction: column; gap: 0.5rem;"><div style="flex: 1; background: rgba(16, 185, 129, 0.08); border: 1px solid #10B981; border-radius: 12px; padding: 0.75rem; text-align: center;"><div style="font-family: 'Plus Jakarta Sans', sans-serif; font-size: 1.25rem; font-weight: 700; color: #10B981;">{accepted}</div><div style="font-size: 0.6rem; color: #10B981; text-transform: uppercase; font-weight: 600;">Accepted</div></div><div style="flex: 1; background: rgba(148, 163, 184, 0.1); border: 1px solid #94A3B8; border-radius: 12px; padding: 0.75rem; text-align: center;"><div style="font-family: 'Plus Jakarta Sans', sans-serif; font-size: 1.25rem; font-weight: 700; color: #94A3B8;">{rejected}</div><div style="font-size: 0.6rem; color: #94A3B8; text-transform: uppercase; font-weight: 600;">Rejected</div></div></div>'''

# Combine all parts
pipeline_html = '<div style="display: flex; gap: 0.75rem; overflow-x: auto; padding: 1rem 0;">' + ''.join(stage_cards) + outcomes_html + '</div>'
st.markdown(pipeline_html, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# Filter tabs
st.markdown(section_header("Applications"), unsafe_allow_html=True)

tab_all, tab_active, tab_completed = st.tabs(["📋 All", "🔥 Active", "✅ Completed"])

def render_applications(apps, key_prefix: str = ""):
    """Render application cards."""
    if not apps:
        st.markdown(empty_state(
            "📭",
            "No applications here",
            "Save jobs from the Search page to start tracking your applications."
        ), unsafe_allow_html=True)
        return

    for app in apps:
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

        with st.expander(f"**{app.job.title}** at {app.job.company}", expanded=False):
            col1, col2 = st.columns([2, 1])

            with col1:
                # Status selector with custom styling
                new_status = st.selectbox(
                    "Status",
                    options=APPLICATION_STATUSES,
                    index=APPLICATION_STATUSES.index(app.status),
                    key=f"{key_prefix}status_{app.id}"
                )

                # Applied date
                applied_date = st.date_input(
                    "Applied Date",
                    value=app.applied_date or date.today(),
                    key=f"{key_prefix}applied_{app.id}"
                )

                # Notes
                notes = st.text_area(
                    "Notes",
                    value=app.notes,
                    key=f"{key_prefix}notes_{app.id}",
                    placeholder="Add notes about this application...",
                    height=100
                )

            with col2:
                # Next step
                st.markdown("""
                <div style="font-family: 'Plus Jakarta Sans', sans-serif; font-size: 0.75rem;
                            text-transform: uppercase; letter-spacing: 0.05em;
                            color: #94A3B8; margin-bottom: 0.5rem;">
                    Next Step
                </div>
                """, unsafe_allow_html=True)

                next_step = st.text_input(
                    "Next Step",
                    value=app.next_step or "",
                    key=f"{key_prefix}next_{app.id}",
                    placeholder="e.g., Follow up email",
                    label_visibility="collapsed"
                )

                next_date = st.date_input(
                    "Due Date",
                    value=app.next_step_date,
                    key=f"{key_prefix}nextdate_{app.id}"
                )

                # View job button
                if app.job.id:
                    full_job = db.get_job(app.job.id)
                    if full_job and full_job.url:
                        job_url = safe_url(full_job.url)
                        st.markdown(f"""
                        <a href="{job_url}" target="_blank"
                           style="display: block; padding: 0.75rem; background: rgba(8, 145, 178, 0.1);
                                  border: 1px solid rgba(8, 145, 178, 0.2); border-radius: 8px;
                                  text-align: center; color: #0891B2; font-size: 0.875rem;
                                  text-decoration: none; margin-top: 1rem; font-weight: 600;">
                            View Job Posting →
                        </a>
                        """, unsafe_allow_html=True)

            # Action buttons
            st.markdown("<br>", unsafe_allow_html=True)
            col_save, col_delete = st.columns(2)

            with col_save:
                if st.button("💾 Save Changes", key=f"{key_prefix}save_{app.id}", type="primary", use_container_width=True):
                    app.status = new_status
                    app.applied_date = applied_date
                    app.notes = notes
                    app.next_step = next_step if next_step else None
                    app.next_step_date = next_date
                    db.save_application(app)
                    st.toast("Application updated!")
                    st.rerun()

            with col_delete:
                if st.button("🗑️ Delete", key=f"{key_prefix}delete_{app.id}", use_container_width=True):
                    db.delete_application(app.id)
                    st.toast("Application deleted")
                    st.rerun()


with tab_all:
    applications = db.get_applications()
    render_applications(applications, key_prefix="all_")

with tab_active:
    active_statuses = ["Saved", "Applied", "Phone Screen", "Interview", "Offer"]
    applications = [a for a in db.get_applications() if a.status in active_statuses]
    render_applications(applications, key_prefix="active_")

with tab_completed:
    completed_statuses = ["Accepted", "Rejected", "Withdrawn"]
    applications = [a for a in db.get_applications() if a.status in completed_statuses]
    render_applications(applications, key_prefix="completed_")

# Statistics visualization
if total > 0:
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown(section_header("Statistics"), unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)

    with col1:
        response_rate = (stats.get("Phone Screen", 0) + stats.get("Interview", 0) +
                        stats.get("Offer", 0) + stats.get("Accepted", 0)) / max(stats.get("Applied", 0), 1) * 100
        st.markdown(f"""
        <div style="background: #FFFFFF; border: 1px solid #E2E8F0;
                    border-radius: 16px; padding: 1.5rem; text-align: center;">
            <div style="font-family: 'Plus Jakarta Sans', sans-serif; font-size: 2rem; font-weight: 700;
                        color: #6366F1;">{response_rate:.0f}%</div>
            <div style="font-size: 0.75rem; color: #94A3B8; text-transform: uppercase; font-weight: 600;">Response Rate</div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        interview_rate = (stats.get("Interview", 0) + stats.get("Offer", 0) +
                         stats.get("Accepted", 0)) / max(total, 1) * 100
        st.markdown(f"""
        <div style="background: #FFFFFF; border: 1px solid #E2E8F0;
                    border-radius: 16px; padding: 1.5rem; text-align: center;">
            <div style="font-family: 'Plus Jakarta Sans', sans-serif; font-size: 2rem; font-weight: 700;
                        color: #F97316;">{interview_rate:.0f}%</div>
            <div style="font-size: 0.75rem; color: #94A3B8; text-transform: uppercase; font-weight: 600;">Interview Rate</div>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        success_rate = stats.get("Accepted", 0) / max(total, 1) * 100
        st.markdown(f"""
        <div style="background: #FFFFFF; border: 1px solid #E2E8F0;
                    border-radius: 16px; padding: 1.5rem; text-align: center;">
            <div style="font-family: 'Plus Jakarta Sans', sans-serif; font-size: 2rem; font-weight: 700;
                        color: #10B981;">{success_rate:.0f}%</div>
            <div style="font-size: 0.75rem; color: #94A3B8; text-transform: uppercase; font-weight: 600;">Success Rate</div>
        </div>
        """, unsafe_allow_html=True)
