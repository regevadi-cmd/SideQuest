"""Resume & Cover Letter Page - AI-assisted resume tailoring and cover letter generation."""
import streamlit as st

from config import DB_PATH
from data.db_factory import Database
from styles import inject_styles, hero_section, section_header, empty_state, feature_card
from utils.auth import require_auth, show_user_menu
from utils.navigation import render_navigation

# Page config
st.set_page_config(
    page_title="Resume Tools | SideQuest",
    page_icon="📝",
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
render_navigation(current_page="resume")

# Sidebar (minimal)
with st.sidebar:
    show_user_menu()

# Hero
st.markdown(hero_section(
    "📝 Resume & Cover Letter Tools",
    "AI-powered assistance to help you stand out"
), unsafe_allow_html=True)

# Check for AI setup
profile = db.get_profile()
ai_configured = st.session_state.get("ai_provider") is not None

if not ai_configured:
    st.markdown("""
    <div style="background: rgba(245, 158, 11, 0.08); border: 1px solid rgba(245, 158, 11, 0.2);
                border-radius: 16px; padding: 1.5rem; margin-bottom: 2rem;">
        <div style="display: flex; align-items: center; gap: 1rem;">
            <div style="font-size: 2rem;">⚡</div>
            <div>
                <div style="font-family: 'Plus Jakarta Sans', sans-serif; font-weight: 700; color: #F59E0B;
                            margin-bottom: 0.25rem;">
                    AI Not Configured
                </div>
                <div style="color: #475569; font-size: 0.875rem;">
                    Set up an AI provider in Settings to unlock resume and cover letter tools.
                </div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    if st.button("Configure AI →", type="primary"):
        st.switch_page("pages/5_settings.py")

# Tool cards
col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("""
    <div style="background: linear-gradient(135deg, rgba(249, 115, 22, 0.08) 0%, rgba(249, 115, 22, 0.02) 100%);
                border: 1px solid rgba(249, 115, 22, 0.2); border-radius: 16px; padding: 1.5rem;
                height: 100%;">
        <div style="font-size: 2.5rem; margin-bottom: 0.75rem;">✉️</div>
        <div style="font-family: 'Plus Jakarta Sans', sans-serif; font-size: 1.125rem; font-weight: 700;
                    color: #F97316; margin-bottom: 0.5rem;">Cover Letter Generator</div>
        <div style="color: #475569; font-size: 0.875rem;">
            Create tailored cover letters for specific job applications
        </div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
    <div style="background: linear-gradient(135deg, rgba(8, 145, 178, 0.08) 0%, rgba(8, 145, 178, 0.02) 100%);
                border: 1px solid rgba(8, 145, 178, 0.2); border-radius: 16px; padding: 1.5rem;
                height: 100%;">
        <div style="font-size: 2.5rem; margin-bottom: 0.75rem;">📊</div>
        <div style="font-family: 'Plus Jakarta Sans', sans-serif; font-size: 1.125rem; font-weight: 700;
                    color: #0891B2; margin-bottom: 0.5rem;">Resume Analyzer</div>
        <div style="color: #475569; font-size: 0.875rem;">
            Get AI-powered suggestions to improve your resume
        </div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown("""
    <div style="background: linear-gradient(135deg, rgba(16, 185, 129, 0.08) 0%, rgba(16, 185, 129, 0.02) 100%);
                border: 1px solid rgba(16, 185, 129, 0.2); border-radius: 16px; padding: 1.5rem;
                height: 100%;">
        <div style="font-size: 2.5rem; margin-bottom: 0.75rem;">🔍</div>
        <div style="font-family: 'Plus Jakarta Sans', sans-serif; font-size: 1.125rem; font-weight: 700;
                    color: #10B981; margin-bottom: 0.5rem;">Job Analyzer</div>
        <div style="color: #475569; font-size: 0.875rem;">
            Extract key requirements from any job posting
        </div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# Tabs for different tools
tab_cover, tab_resume, tab_analyze = st.tabs(["✉️ Cover Letter", "📊 Resume Tips", "🔍 Job Analysis"])

with tab_cover:
    st.markdown(section_header("Generate Cover Letter"), unsafe_allow_html=True)

    # Select from saved jobs or paste description
    applications = db.get_applications()
    saved_jobs = [a for a in applications if a.status == "Saved"]

    input_method = st.radio(
        "Job Source",
        ["Select from saved jobs", "Paste job description"],
        horizontal=True,
        label_visibility="collapsed"
    )

    job_description = ""
    job_title = ""
    company_name = ""

    if input_method == "Select from saved jobs" and saved_jobs:
        job_options = {f"{a.job.title} at {a.job.company}": a for a in saved_jobs}
        selected = st.selectbox("Select Job", options=list(job_options.keys()))
        if selected:
            app = job_options[selected]
            full_job = db.get_job(app.job_id)
            if full_job:
                job_description = full_job.description
                job_title = full_job.title
                company_name = full_job.company

                st.markdown(f"""
                <div style="background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 12px;
                            padding: 1rem; margin-top: 1rem;">
                    <div style="color: #94A3B8; font-size: 0.75rem; text-transform: uppercase;
                                margin-bottom: 0.5rem; font-weight: 600;">Selected Job</div>
                    <div style="font-family: 'Plus Jakarta Sans', sans-serif; color: #0F172A; font-weight: 700;">
                        {job_title}
                    </div>
                    <div style="color: #0891B2; font-size: 0.875rem; font-weight: 600;">{company_name}</div>
                </div>
                """, unsafe_allow_html=True)
    else:
        job_title = st.text_input("Job Title", placeholder="e.g., Software Engineer Intern")
        company_name = st.text_input("Company Name", placeholder="e.g., Google")
        job_description = st.text_area(
            "Job Description",
            height=200,
            placeholder="Paste the full job description here..."
        )

    # Cover letter options
    st.markdown("<br>", unsafe_allow_html=True)
    col_tone, col_length = st.columns(2)

    with col_tone:
        tone = st.selectbox("Tone", ["Professional", "Enthusiastic", "Confident", "Humble"])

    with col_length:
        length = st.selectbox("Length", ["Short (150 words)", "Medium (250 words)", "Long (400 words)"])

    # User's background
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown(section_header("Your Background"), unsafe_allow_html=True)

    if profile and profile.resume_text:
        st.markdown("""
        <div style="background: rgba(16, 185, 129, 0.08); border: 1px solid rgba(16, 185, 129, 0.2);
                    border-radius: 12px; padding: 1rem; margin-bottom: 1rem;">
            <div style="color: #10B981; font-size: 0.875rem; font-weight: 600;">
                ✓ Using resume from your profile
            </div>
        </div>
        """, unsafe_allow_html=True)
        with st.expander("View/Edit Resume"):
            resume_text = st.text_area("Resume", value=profile.resume_text, height=300, label_visibility="collapsed")
    else:
        resume_text = st.text_area(
            "Resume / Background",
            height=200,
            placeholder="Paste your resume or describe your background..."
        )

    st.markdown("<br>", unsafe_allow_html=True)

    if st.button("✨ Generate Cover Letter", type="primary", disabled=not ai_configured, use_container_width=True):
        if not job_description:
            st.error("Please provide a job description")
        elif not resume_text:
            st.error("Please provide your resume or background")
        else:
            with st.spinner(""):
                st.markdown("""
                <div style="text-align: center; padding: 2rem;">
                    <div style="font-family: 'Plus Jakarta Sans', sans-serif; color: #0891B2;
                                animation: pulse 1.5s ease-in-out infinite; font-weight: 600;">
                        ✨ Crafting your cover letter...
                    </div>
                </div>
                """, unsafe_allow_html=True)

                try:
                    from ai.resume_helper import generate_cover_letter
                    cover_letter = generate_cover_letter(
                        job_title=job_title,
                        company=company_name,
                        job_description=job_description,
                        resume=resume_text,
                        tone=tone.lower(),
                        length=length.split()[0].lower()
                    )

                    st.markdown("""
                    <div style="font-family: 'Plus Jakarta Sans', sans-serif; font-size: 1.25rem;
                                font-weight: 700; color: #0F172A; margin: 1.5rem 0 1rem 0;">
                        Generated Cover Letter
                    </div>
                    """, unsafe_allow_html=True)

                    st.markdown(f"""
                    <div style="background: #FFFFFF; border: 1px solid #E2E8F0;
                                border-radius: 16px; padding: 1.5rem; line-height: 1.7; color: #475569;">
                        {cover_letter.replace(chr(10), '<br>')}
                    </div>
                    """, unsafe_allow_html=True)

                    st.text_area("Copy from here:", value=cover_letter, height=300, label_visibility="collapsed")

                except Exception as e:
                    st.error(f"Generation failed: {str(e)}")

with tab_resume:
    st.markdown(section_header("Resume Improvement Suggestions"), unsafe_allow_html=True)

    # Input resume
    if profile and profile.resume_text:
        resume_for_tips = profile.resume_text
        st.markdown("""
        <div style="background: rgba(16, 185, 129, 0.08); border: 1px solid rgba(16, 185, 129, 0.2);
                    border-radius: 12px; padding: 1rem; margin-bottom: 1rem;">
            <div style="color: #10B981; font-size: 0.875rem; font-weight: 600;">
                ✓ Using resume from your profile
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        resume_for_tips = st.text_area(
            "Your Resume",
            height=300,
            placeholder="Paste your resume here..."
        )

    # Optional: target job
    st.markdown("<br>", unsafe_allow_html=True)
    target_job = st.text_area(
        "Target Job Description (optional)",
        height=150,
        placeholder="Paste a job description to get targeted suggestions...",
        help="Adding a target job helps provide more specific recommendations"
    )

    st.markdown("<br>", unsafe_allow_html=True)

    if st.button("🔍 Analyze Resume", type="primary", disabled=not ai_configured, use_container_width=True):
        if not resume_for_tips:
            st.error("Please provide your resume")
        else:
            with st.spinner(""):
                st.markdown("""
                <div style="text-align: center; padding: 2rem;">
                    <div style="font-family: 'Plus Jakarta Sans', sans-serif; color: #0891B2;
                                animation: pulse 1.5s ease-in-out infinite; font-weight: 600;">
                        🔍 Analyzing your resume...
                    </div>
                </div>
                """, unsafe_allow_html=True)

                try:
                    from ai.resume_helper import analyze_resume
                    suggestions = analyze_resume(
                        resume=resume_for_tips,
                        target_job=target_job if target_job else None
                    )

                    st.markdown(f"""
                    <div style="background: #FFFFFF; border: 1px solid #E2E8F0;
                                border-radius: 16px; padding: 1.5rem; line-height: 1.7; color: #475569;">
                        {suggestions.replace(chr(10), '<br>')}
                    </div>
                    """, unsafe_allow_html=True)

                except Exception as e:
                    st.error(f"Analysis failed: {str(e)}")

with tab_analyze:
    st.markdown(section_header("Job Description Analysis"), unsafe_allow_html=True)

    st.markdown("""
    <div style="color: #475569; margin-bottom: 1.5rem;">
        Extract key requirements and skills from any job posting to understand what employers are looking for.
    </div>
    """, unsafe_allow_html=True)

    job_to_analyze = st.text_area(
        "Job Description",
        height=300,
        placeholder="Paste a job description to analyze..."
    )

    st.markdown("<br>", unsafe_allow_html=True)

    if st.button("📊 Analyze Job", type="primary", disabled=not ai_configured, use_container_width=True):
        if not job_to_analyze:
            st.error("Please provide a job description")
        else:
            with st.spinner(""):
                st.markdown("""
                <div style="text-align: center; padding: 2rem;">
                    <div style="font-family: 'Plus Jakarta Sans', sans-serif; color: #0891B2;
                                animation: pulse 1.5s ease-in-out infinite; font-weight: 600;">
                        📊 Extracting insights...
                    </div>
                </div>
                """, unsafe_allow_html=True)

                try:
                    from ai.job_analyzer import analyze_job_description
                    analysis = analyze_job_description(job_to_analyze)

                    col1, col2 = st.columns(2)

                    with col1:
                        st.markdown("""
                        <div style="font-family: 'Plus Jakarta Sans', sans-serif; font-weight: 700; color: #F97316;
                                    margin-bottom: 1rem;">Required Skills</div>
                        """, unsafe_allow_html=True)

                        for skill in analysis.get("required_skills", []):
                            st.markdown(f"""
                            <div style="display: inline-block; padding: 0.5rem 1rem;
                                        background: rgba(249, 115, 22, 0.1); border-radius: 20px;
                                        color: #F97316; font-size: 0.875rem; margin: 0.25rem; font-weight: 600;">
                                {skill}
                            </div>
                            """, unsafe_allow_html=True)

                        st.markdown("<br><br>", unsafe_allow_html=True)

                        st.markdown("""
                        <div style="font-family: 'Plus Jakarta Sans', sans-serif; font-weight: 700; color: #0891B2;
                                    margin-bottom: 1rem;">Nice to Have</div>
                        """, unsafe_allow_html=True)

                        for skill in analysis.get("nice_to_have", []):
                            st.markdown(f"""
                            <div style="display: inline-block; padding: 0.5rem 1rem;
                                        background: rgba(8, 145, 178, 0.1); border-radius: 20px;
                                        color: #0891B2; font-size: 0.875rem; margin: 0.25rem; font-weight: 600;">
                                {skill}
                            </div>
                            """, unsafe_allow_html=True)

                    with col2:
                        st.markdown("""
                        <div style="font-family: 'Plus Jakarta Sans', sans-serif; font-weight: 700; color: #10B981;
                                    margin-bottom: 1rem;">Key Responsibilities</div>
                        """, unsafe_allow_html=True)

                        for resp in analysis.get("responsibilities", []):
                            st.markdown(f"""
                            <div style="padding: 0.75rem; background: #FFFFFF;
                                        border-left: 3px solid #10B981; border-radius: 0 8px 8px 0;
                                        margin-bottom: 0.5rem; color: #475569; font-size: 0.875rem;
                                        border: 1px solid #E2E8F0; border-left: 3px solid #10B981;">
                                {resp}
                            </div>
                            """, unsafe_allow_html=True)

                        if analysis.get("salary_estimate"):
                            st.markdown("<br>", unsafe_allow_html=True)
                            st.markdown(f"""
                            <div style="background: rgba(245, 158, 11, 0.08); border: 1px solid rgba(245, 158, 11, 0.2);
                                        border-radius: 12px; padding: 1rem;">
                                <div style="font-family: 'Plus Jakarta Sans', sans-serif; font-weight: 700;
                                            color: #F59E0B; margin-bottom: 0.25rem;">Estimated Salary</div>
                                <div style="color: #475569;">{analysis["salary_estimate"]}</div>
                            </div>
                            """, unsafe_allow_html=True)

                except Exception as e:
                    st.error(f"Analysis failed: {str(e)}")
