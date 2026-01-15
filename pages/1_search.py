"""Job Search Page - Search and browse job listings."""
import streamlit as st
from datetime import datetime

from config import DB_PATH, JOB_TYPES, DEFAULT_RADIUS_MILES
from data.db_factory import Database
from data.models import Job, Application
from styles import (
    inject_styles, hero_section, section_header, job_card, empty_state,
    skeleton_job_card, loading_indicator
)
from utils.auth import require_auth, show_user_menu
from utils.navigation import render_navigation
from utils.settings import load_settings
from utils.sanitize import safe_html, safe_url
from utils.rate_limiter import check_search_rate_limit

# Page config
st.set_page_config(
    page_title="Search Jobs | SideQuest",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
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

# Load saved settings from database
load_settings(db)

# Top navigation
render_navigation(current_page="search")

# Sidebar for filters only
with st.sidebar:
    show_user_menu()
    st.markdown("---")

# Get user data
profile = db.get_profile()
locations = db.get_locations()

if not locations:
    st.markdown(hero_section("🔍 Job Search", "Find opportunities near you"), unsafe_allow_html=True)
    st.markdown(empty_state(
        "📍",
        "No locations set up",
        "Add your university or search location to start finding jobs."
    ), unsafe_allow_html=True)
    if st.button("Add Location →", type="primary"):
        st.switch_page("pages/5_settings.py")
    st.stop()

# Hero
st.markdown(hero_section(
    "🔍 Job Search",
    "Discover opportunities that match your skills and schedule"
), unsafe_allow_html=True)

# Search filters in sidebar
with st.sidebar:
    st.markdown(section_header("Filters"), unsafe_allow_html=True)

    # Location selector
    location_options = {loc.name: loc for loc in locations}
    selected_loc_name = st.selectbox(
        "📍 Location",
        options=list(location_options.keys()),
        index=0
    )
    selected_location = location_options[selected_loc_name]

    # Radius
    radius = st.slider(
        "Search Radius",
        min_value=1,
        max_value=50,
        value=selected_location.radius_miles or DEFAULT_RADIUS_MILES,
        format="%d miles"
    )

    st.markdown("<br>", unsafe_allow_html=True)

    # Job sources selector
    st.markdown("""
    <div style="font-family: 'Plus Jakarta Sans', sans-serif; font-size: 0.75rem; text-transform: uppercase;
                letter-spacing: 0.05em; color: #94A3B8; margin-bottom: 0.5rem;">
        Job Sources
    </div>
    """, unsafe_allow_html=True)

    # Build source options - include university if configured
    base_sources = ["Indeed", "LinkedIn", "Glassdoor", "College Recruiter", "WayUp"]
    uni_config = st.session_state.get("university_job_board", {})
    uni_source_name = None
    if uni_config.get("url"):
        uni_name = uni_config.get("name", "University")
        uni_source_name = f"🎓 {uni_name}"
        base_sources.append(uni_source_name)

    # Get default sources from profile preferences
    default_sources = ["Indeed", "LinkedIn", "Glassdoor"]
    if profile and profile.preferred_job_sources:
        # Convert profile format to search format
        default_sources = []
        for src in profile.preferred_job_sources:
            if src.startswith("University (") and uni_source_name:
                default_sources.append(uni_source_name)
            elif src in base_sources:
                default_sources.append(src)
        # If none valid, use defaults
        if not default_sources:
            default_sources = ["Indeed", "LinkedIn", "Glassdoor"]

    job_sources = st.multiselect(
        "Sources",
        options=base_sources,
        default=default_sources,
        label_visibility="collapsed"
    )

    help_text = "College Recruiter & WayUp specialize in student/entry-level jobs"
    if uni_config.get("url"):
        help_text += f" · 🎓 = {uni_config.get('name', 'University')} job board"

    st.markdown(f"""
    <div style="font-size: 0.7rem; color: #94A3B8; margin-top: 0.25rem;">
        {help_text}
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Job type filter
    job_types = st.multiselect(
        "Job Type",
        options=JOB_TYPES,
        default=profile.preferred_job_types if profile else ["Part-time", "Internship"]
    )

    # Keywords
    keywords = st.text_input("🔎 Keywords", placeholder="e.g., software, retail, tutor")

    # Salary filter
    min_salary = st.number_input(
        "💰 Min Hourly Rate ($)",
        min_value=0.0,
        value=profile.min_hourly_rate if profile and profile.min_hourly_rate else 0.0,
        step=1.0,
        format="%.0f"
    )

    # Schedule filter
    has_schedule = profile and profile.schedule_blocks
    schedule_only = st.checkbox(
        "✓ Schedule compatible only",
        value=has_schedule,
        disabled=not has_schedule,
        help="Only show jobs that fit your class schedule" if has_schedule else "Set up your schedule in Profile first"
    )

    st.markdown("<br>", unsafe_allow_html=True)

    # Search button
    search_clicked = st.button("🔍 Search Jobs", type="primary", use_container_width=True)

# Main content - sanitize location name to prevent XSS
st.markdown(f"""
<div style="display: flex; align-items: center; gap: 0.5rem; margin-bottom: 1.5rem;">
    <span style="color: #475569;">Searching near</span>
    <span style="font-family: 'Plus Jakarta Sans', sans-serif; font-weight: 600; color: #0891B2;">
        {safe_html(selected_location.name)}
    </span>
    <span style="color: #94A3B8;">· {radius} mile radius</span>
</div>
""", unsafe_allow_html=True)

# Search state
if "search_results" not in st.session_state:
    st.session_state.search_results = []

if search_clicked:
    if not job_sources:
        st.error("Please select at least one job source")
    else:
        # Check rate limit
        allowed, rate_msg = check_search_rate_limit()
        if not allowed:
            st.error(rate_msg)
            st.stop()

        # Import scrapers
        from scrapers.indeed import IndeedScraper
        from scrapers.linkedin import LinkedInScraper
        from scrapers.glassdoor import GlassdoorScraper
        from scrapers.collegerecruiter import CollegeRecruiterScraper
        from scrapers.wayup import WayUpScraper
        from scrapers.university import UniversityJobBoardScraper

        all_jobs = []
        errors = []

        # Create progress container
        progress_container = st.empty()
        status_container = st.empty()
        skeleton_container = st.empty()

        # Show skeleton loaders while searching
        skeleton_container.markdown(skeleton_job_card(5), unsafe_allow_html=True)

        total_sources = len(job_sources)
        for idx, source in enumerate(job_sources):
            progress = (idx + 1) / total_sources

            progress_container.progress(progress, text=f"Searching {source}...")

            status_container.markdown(f"""
            <div style="text-align: center; padding: 1rem;">
                <div style="font-family: 'Plus Jakarta Sans', sans-serif; font-size: 1rem; color: #0891B2;">
                    🔍 Searching {source}... ({idx + 1}/{total_sources})
                </div>
            </div>
            """, unsafe_allow_html=True)

            try:
                if source == "Indeed":
                    scraper = IndeedScraper()
                elif source == "LinkedIn":
                    scraper = LinkedInScraper()
                elif source == "Glassdoor":
                    scraper = GlassdoorScraper()
                elif source == "College Recruiter":
                    scraper = CollegeRecruiterScraper()
                elif source == "WayUp":
                    scraper = WayUpScraper()
                elif source.startswith("🎓"):
                    # University job board
                    uni_config = st.session_state.get("university_job_board", {})
                    if uni_config.get("url"):
                        scraper = UniversityJobBoardScraper(
                            university_name=uni_config.get("name", "University"),
                            job_board_url=uni_config.get("url")
                        )
                        # Add auth cookie if configured
                        if uni_config.get("use_auth") and uni_config.get("auth_cookie"):
                            scraper.headers["Cookie"] = uni_config.get("auth_cookie")
                    else:
                        continue
                else:
                    continue

                jobs = scraper.search(
                    query=keywords or "student jobs",
                    location=selected_location.address,
                    radius=radius,
                    job_types=job_types if job_types else None,
                    max_results=30  # Limit per source
                )

                all_jobs.extend(jobs)

            except Exception as e:
                errors.append(f"{source}: {str(e)}")

        # Clear progress and skeleton loaders
        progress_container.empty()
        status_container.empty()
        skeleton_container.empty()

        # Save all jobs to database
        for job in all_jobs:
            db.save_job(job)

        # Deduplicate by title + company
        seen = set()
        unique_jobs = []
        for job in all_jobs:
            key = (job.title.lower(), job.company.lower())
            if key not in seen:
                seen.add(key)
                unique_jobs.append(job)

        st.session_state.search_results = unique_jobs

        # Show summary
        if unique_jobs:
            source_counts = {}
            for job in unique_jobs:
                source_counts[job.source] = source_counts.get(job.source, 0) + 1

            summary_parts = [f"{count} from {source.title()}" for source, count in source_counts.items()]
            st.success(f"Found {len(unique_jobs)} jobs: {', '.join(summary_parts)}")

        if errors:
            for error in errors:
                st.warning(f"⚠️ {error}")

# Display results
results = st.session_state.search_results

if results:
    # Results header
    st.markdown(f"""
    <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 1.5rem;">
        <div style="font-family: 'Plus Jakarta Sans', sans-serif; font-size: 1.25rem; font-weight: 700; color: #0F172A;">
            {len(results)} Jobs Found
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Sort options
    col1, col2 = st.columns([3, 1])
    with col2:
        sort_by = st.selectbox(
            "Sort by",
            ["Match Score", "Posted Date", "Company", "Salary", "Source"],
            index=0,
            label_visibility="collapsed"
        )

    if sort_by == "Match Score":
        results = sorted(results, key=lambda j: j.match_score or 0, reverse=True)
    elif sort_by == "Posted Date":
        results = sorted(results, key=lambda j: j.posted_date or datetime.min.date(), reverse=True)
    elif sort_by == "Company":
        results = sorted(results, key=lambda j: j.company.lower())
    elif sort_by == "Salary":
        results = sorted(results, key=lambda j: j.salary_min or 0, reverse=True)
    elif sort_by == "Source":
        results = sorted(results, key=lambda j: j.source.lower())

    # Display job cards
    for job in results:
        # Build tags
        tags = []
        if job.source:
            tags.append(job.source.title())
        if job.job_type:
            tags.append(job.job_type)

        # Create card HTML
        card_html = job_card(
            title=job.title,
            company=job.company,
            location=job.location,
            tags=tags,
            salary=job.salary_text,
            match_score=job.match_score,
            url=job.url,
            schedule_ok=job.schedule_compatible
        )

        col1, col2 = st.columns([5, 1])

        with col1:
            st.markdown(card_html, unsafe_allow_html=True)

        with col2:
            # Action buttons
            existing_app = db.get_application_for_job(job.id) if job.id else None

            if existing_app:
                st.markdown(f"""
                <div style="padding: 0.5rem 1rem; background: rgba(16, 185, 129, 0.1);
                            border: 1px solid rgba(16, 185, 129, 0.2); border-radius: 8px;
                            font-size: 0.75rem; color: #10B981; text-align: center;
                            margin-top: 1rem; font-weight: 600;">
                    {existing_app.status}
                </div>
                """, unsafe_allow_html=True)
            else:
                if st.button("💾 Save", key=f"save_{job.unique_key}", use_container_width=True):
                    saved_job = db.save_job(job)
                    app = Application(job_id=saved_job.id, status="Saved")
                    db.save_application(app)
                    st.toast(f"Saved {job.title}!")
                    st.rerun()

        # Description expander
        if job.description:
            with st.expander("View Description"):
                st.markdown(f"""
                <div style="color: #475569; font-size: 0.9rem; line-height: 1.6;">
                    {job.description}
                </div>
                """, unsafe_allow_html=True)

else:
    # No results state
    st.markdown(empty_state(
        "🔍",
        "Ready to search",
        "Set your filters and click 'Search Jobs' to find opportunities near you."
    ), unsafe_allow_html=True)

    # Show recently found jobs from database
    recent_jobs = db.get_jobs(limit=5)
    if recent_jobs:
        st.markdown(section_header("Recently Found"), unsafe_allow_html=True)

        for job in recent_jobs:
            st.markdown(f"""
            <div style="display: flex; align-items: center; gap: 1rem; padding: 1rem;
                        background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 12px; margin-bottom: 0.5rem;">
                <div style="flex: 1;">
                    <div style="font-family: 'Plus Jakarta Sans', sans-serif; font-weight: 600; color: #0F172A;">
                        {job.title}
                    </div>
                    <div style="font-size: 0.875rem; color: #475569;">
                        {job.company} · {job.source}
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
