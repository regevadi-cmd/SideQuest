"""Profile Page - User profile with major, skills, and schedule."""
import streamlit as st

from config import DB_PATH, JOB_TYPES
from data.db_factory import Database
from data.models import Profile, ScheduleBlock
from utils.schedule import parse_schedule, format_availability_summary, DAYS_OF_WEEK
from styles import inject_styles, hero_section, section_header
from utils.auth import require_auth, show_user_menu
from utils.navigation import render_navigation

# Page config
st.set_page_config(
    page_title="Profile | SideQuest",
    page_icon="👤",
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
render_navigation(current_page="profile")

# Sidebar (minimal)
with st.sidebar:
    show_user_menu()

# Hero
st.markdown(hero_section(
    "👤 Your Profile",
    "Set up your profile to get personalized job matches"
), unsafe_allow_html=True)

# Load existing profile
profile = db.get_profile()
if not profile:
    profile = Profile()

# Basic info section
st.markdown(section_header("Basic Information"), unsafe_allow_html=True)

col1, col2 = st.columns(2)

with col1:
    name = st.text_input("Name", value=profile.name, placeholder="Your name")
    major = st.text_input("Major / Field of Study", value=profile.major, placeholder="e.g., Computer Science")

with col2:
    min_rate = st.number_input(
        "Minimum Hourly Rate ($)",
        min_value=0.0,
        value=profile.min_hourly_rate or 0.0,
        step=1.0,
        format="%.0f"
    )
    max_hours = st.number_input(
        "Max Hours Per Week",
        min_value=0,
        max_value=60,
        value=profile.max_hours_per_week or 20,
        step=1
    )

# Skills section
st.markdown("<br>", unsafe_allow_html=True)
st.markdown(section_header("Skills"), unsafe_allow_html=True)

st.markdown("""
<div style="color: #475569; font-size: 0.875rem; margin-bottom: 1rem;">
    List your skills - these help match you with relevant jobs
</div>
""", unsafe_allow_html=True)

skills_text = st.text_area(
    "Your Skills (one per line)",
    value="\n".join(profile.skills) if profile.skills else "",
    height=120,
    placeholder="Python\nCustomer Service\nMicrosoft Excel\nData Analysis\n...",
    label_visibility="collapsed"
)

# Interests section
st.markdown("<br>", unsafe_allow_html=True)
st.markdown(section_header("Job Interests"), unsafe_allow_html=True)

interests_text = st.text_area(
    "What types of work interest you? (one per line)",
    value="\n".join(profile.interests) if profile.interests else "",
    height=100,
    placeholder="Software Development\nResearch Assistant\nTutoring\nRetail\n...",
    label_visibility="collapsed"
)

# Preferred job types
st.markdown("<br>", unsafe_allow_html=True)
st.markdown(section_header("Preferred Job Types"), unsafe_allow_html=True)

# Display as styled chips
preferred_types = st.multiselect(
    "Select all that apply",
    options=JOB_TYPES,
    default=profile.preferred_job_types if profile.preferred_job_types else ["Part-time", "Internship"],
    label_visibility="collapsed"
)

# Preferred job sources
st.markdown("<br>", unsafe_allow_html=True)
st.markdown(section_header("Preferred Job Sources"), unsafe_allow_html=True)

st.markdown("""
<div style="color: #475569; font-size: 0.875rem; margin-bottom: 1rem;">
    Select your preferred job boards to search by default
</div>
""", unsafe_allow_html=True)

# Build source options - include university if configured
from utils.settings import load_settings
load_settings(db)

base_sources = ["Indeed", "LinkedIn", "Glassdoor", "College Recruiter", "WayUp"]
uni_config = st.session_state.get("university_job_board", {})
if uni_config.get("url"):
    uni_name = uni_config.get("name", "University")
    base_sources.append(f"University ({uni_name})")

# Default sources if none saved
default_sources = profile.preferred_job_sources if profile.preferred_job_sources else ["Indeed", "LinkedIn", "Glassdoor"]
# Filter to only include valid options
default_sources = [s for s in default_sources if s in base_sources]

preferred_sources = st.multiselect(
    "Select job sources",
    options=base_sources,
    default=default_sources,
    label_visibility="collapsed"
)

st.markdown("""
<div style="font-size: 0.75rem; color: #94A3B8; margin-top: 0.25rem;">
    College Recruiter & WayUp specialize in student/entry-level jobs
</div>
""", unsafe_allow_html=True)

# Class schedule
st.markdown("<br>", unsafe_allow_html=True)
st.markdown(section_header("Class Schedule"), unsafe_allow_html=True)

st.markdown("""
<div style="background: rgba(8, 145, 178, 0.08); border: 1px solid rgba(8, 145, 178, 0.2);
            border-radius: 12px; padding: 1rem; margin-bottom: 1.5rem;">
    <div style="color: #0891B2; font-size: 0.875rem; font-weight: 600;">
        💡 Add your unavailable times (classes, etc.) to filter out jobs that conflict with your schedule
    </div>
</div>
""", unsafe_allow_html=True)

# Schedule input method
schedule_method = st.radio(
    "Input Method",
    ["Visual Editor", "Text Format"],
    horizontal=True,
    label_visibility="collapsed"
)

schedule_blocks = profile.schedule_blocks.copy() if profile.schedule_blocks else []

if schedule_method == "Visual Editor":
    st.markdown("""
    <div style="font-family: 'Plus Jakarta Sans', sans-serif; font-size: 0.875rem; font-weight: 700;
                color: #0F172A; margin-bottom: 1rem;">
        Add Unavailable Time Block
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3, col4 = st.columns([1, 1, 1, 2])

    with col1:
        new_day = st.selectbox("Day", options=DAYS_OF_WEEK, label_visibility="collapsed")
    with col2:
        new_start = st.time_input("Start", value=None, label_visibility="collapsed")
    with col3:
        new_end = st.time_input("End", value=None, label_visibility="collapsed")
    with col4:
        new_label = st.text_input("Label (optional)", placeholder="e.g., CS101", label_visibility="collapsed")

    if st.button("➕ Add Block", use_container_width=False):
        if new_start and new_end:
            block = ScheduleBlock(
                day=new_day,
                start_time=new_start.strftime("%H:%M"),
                end_time=new_end.strftime("%H:%M"),
                label=new_label if new_label else None
            )
            schedule_blocks.append(block)
            st.toast(f"Added {new_day} {new_start.strftime('%H:%M')}-{new_end.strftime('%H:%M')}")
            st.rerun()

    # Display current blocks
    if schedule_blocks:
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("""
        <div style="font-family: 'Plus Jakarta Sans', sans-serif; font-size: 0.875rem; font-weight: 700;
                    color: #0F172A; margin-bottom: 1rem;">
            Current Schedule
        </div>
        """, unsafe_allow_html=True)

        for i, block in enumerate(schedule_blocks):
            col1, col2 = st.columns([5, 1])
            with col1:
                label_str = f" - {block.label}" if block.label else ""
                st.markdown(f"""
                <div style="display: flex; align-items: center; gap: 1rem; padding: 0.75rem 1rem;
                            background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 8px; margin-bottom: 0.5rem;">
                    <div style="font-family: 'Plus Jakarta Sans', sans-serif; font-weight: 700; color: #0891B2;
                                min-width: 40px;">{block.day}</div>
                    <div style="color: #0F172A;">{block.start_time} - {block.end_time}</div>
                    <div style="color: #94A3B8;">{label_str}</div>
                </div>
                """, unsafe_allow_html=True)
            with col2:
                if st.button("🗑️", key=f"del_block_{i}"):
                    schedule_blocks.pop(i)
                    st.rerun()

else:
    # Text format input
    schedule_text = st.text_area(
        "Schedule (one per line: Day Start-End Label)",
        value="\n".join(
            f"{b.day} {b.start_time}-{b.end_time} {b.label or ''}"
            for b in schedule_blocks
        ),
        height=150,
        placeholder="Mon 9:00-10:30 CS101\nTue 14:00-15:30 Math202\nWed 9:00-10:30 CS101"
    )

    if schedule_text:
        schedule_blocks = parse_schedule(schedule_text)
        if schedule_blocks:
            st.markdown(f"""
            <div style="background: rgba(16, 185, 129, 0.08); border: 1px solid rgba(16, 185, 129, 0.2);
                        border-radius: 8px; padding: 0.75rem; margin-top: 0.5rem;">
                <div style="color: #10B981; font-size: 0.875rem; font-weight: 600;">
                    ✓ Parsed {len(schedule_blocks)} time blocks
                </div>
            </div>
            """, unsafe_allow_html=True)

# Availability summary
if schedule_blocks:
    st.markdown("<br>", unsafe_allow_html=True)
    summary = format_availability_summary(schedule_blocks)
    st.markdown(f"""
    <div style="background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 12px; padding: 1rem;">
        <div style="font-family: 'Plus Jakarta Sans', sans-serif; font-size: 0.75rem; text-transform: uppercase;
                    letter-spacing: 0.05em; color: #94A3B8; margin-bottom: 0.5rem; font-weight: 600;">
            Availability Summary
        </div>
        <div style="color: #475569; font-size: 0.875rem; white-space: pre-line;">
            {summary}
        </div>
    </div>
    """, unsafe_allow_html=True)

# Resume section
st.markdown("<br>", unsafe_allow_html=True)
st.markdown(section_header("Resume"), unsafe_allow_html=True)

st.markdown("""
<div style="color: #475569; font-size: 0.875rem; margin-bottom: 1rem;">
    Paste your resume to enable AI-powered cover letter generation and job matching
</div>
""", unsafe_allow_html=True)

resume_text = st.text_area(
    "Resume Text",
    value=profile.resume_text or "",
    height=300,
    placeholder="Paste your full resume here...",
    label_visibility="collapsed"
)

# Save button
st.markdown("<br>", unsafe_allow_html=True)
st.markdown("---")

if st.button("💾 Save Profile", type="primary", use_container_width=True):
    # Parse inputs
    skills = [s.strip() for s in skills_text.split("\n") if s.strip()]
    interests = [i.strip() for i in interests_text.split("\n") if i.strip()]

    # Update profile
    profile.name = name
    profile.major = major
    profile.skills = skills
    profile.interests = interests
    profile.min_hourly_rate = min_rate if min_rate > 0 else None
    profile.max_hours_per_week = max_hours if max_hours > 0 else None
    profile.preferred_job_types = preferred_types
    profile.preferred_job_sources = preferred_sources
    profile.schedule_blocks = schedule_blocks
    profile.resume_text = resume_text if resume_text else None

    # Save to database
    db.save_profile(profile)

    st.toast("Profile saved!")

    # Show next steps
    if not db.get_locations():
        st.markdown("""
        <div style="background: rgba(8, 145, 178, 0.08); border: 1px solid rgba(8, 145, 178, 0.2);
                    border-radius: 12px; padding: 1rem; margin-top: 1rem;">
            <div style="font-family: 'Plus Jakarta Sans', sans-serif; font-weight: 700; color: #0891B2;
                        margin-bottom: 0.25rem;">
                Next Step
            </div>
            <div style="color: #475569; font-size: 0.875rem;">
                Add a search location in Settings to start finding jobs
            </div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Go to Settings →"):
            st.switch_page("pages/5_settings.py")
