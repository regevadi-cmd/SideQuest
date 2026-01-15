"""Settings Page - AI provider configuration and location management."""
import streamlit as st

from config import DB_PATH, DEFAULT_RADIUS_MILES, ANTHROPIC_API_KEY, OPENAI_API_KEY, OLLAMA_ENABLED
from data.db_factory import Database
from data.models import SavedLocation
from utils.location import geocode_address
from utils.settings import load_settings
from styles import inject_styles, hero_section, section_header, empty_state
from utils.auth import require_auth, show_user_menu
from utils.navigation import render_navigation
from utils.sanitize import safe_html, safe_url
from utils.encryption import encrypt_value, decrypt_value, mask_api_key

# Page config
st.set_page_config(
    page_title="Settings | SideQuest",
    page_icon="⚙️",
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

# Load saved settings from database
load_settings(db)

# Top navigation
render_navigation(current_page="settings")

# Sidebar (minimal)
with st.sidebar:
    show_user_menu()

# Hero
st.markdown(hero_section(
    "⚙️ Settings",
    "Configure AI providers and manage your search locations"
), unsafe_allow_html=True)

# AI Provider Configuration
st.markdown(section_header("AI Provider"), unsafe_allow_html=True)

st.markdown("""
<div style="color: #475569; font-size: 0.875rem; margin-bottom: 1.5rem;">
    Configure the AI service for smart job matching, cover letter generation, and resume tools
</div>
""", unsafe_allow_html=True)

# Provider cards - conditionally show Ollama based on environment
if OLLAMA_ENABLED:
    col1, col2, col3 = st.columns(3)
else:
    col1, col2 = st.columns(2)

with col1:
    st.markdown("""
    <div style="background: linear-gradient(135deg, rgba(249, 115, 22, 0.08) 0%, rgba(249, 115, 22, 0.02) 100%);
                border: 1px solid rgba(249, 115, 22, 0.2); border-radius: 16px; padding: 1.25rem;">
        <div style="font-family: 'Plus Jakarta Sans', sans-serif; font-weight: 700; color: #F97316;
                    margin-bottom: 0.25rem;">Claude</div>
        <div style="color: #475569; font-size: 0.75rem;">Anthropic's AI</div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
    <div style="background: linear-gradient(135deg, rgba(16, 185, 129, 0.08) 0%, rgba(16, 185, 129, 0.02) 100%);
                border: 1px solid rgba(16, 185, 129, 0.2); border-radius: 16px; padding: 1.25rem;">
        <div style="font-family: 'Plus Jakarta Sans', sans-serif; font-weight: 700; color: #10B981;
                    margin-bottom: 0.25rem;">OpenAI</div>
        <div style="color: #475569; font-size: 0.75rem;">GPT-5 Models</div>
    </div>
    """, unsafe_allow_html=True)

if OLLAMA_ENABLED:
    with col3:
        st.markdown("""
        <div style="background: linear-gradient(135deg, rgba(8, 145, 178, 0.08) 0%, rgba(8, 145, 178, 0.02) 100%);
                    border: 1px solid rgba(8, 145, 178, 0.2); border-radius: 16px; padding: 1.25rem;">
            <div style="font-family: 'Plus Jakarta Sans', sans-serif; font-weight: 700; color: #0891B2;
                        margin-bottom: 0.25rem;">Ollama</div>
            <div style="color: #475569; font-size: 0.75rem;">Local Models</div>
        </div>
        """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# Provider selection - conditionally include Ollama
if OLLAMA_ENABLED:
    ai_providers = ["Claude (Anthropic)", "OpenAI (GPT-5)", "Ollama (Local)", "None (Disable AI)"]
else:
    ai_providers = ["Claude (Anthropic)", "OpenAI (GPT-5)", "None (Disable AI)"]
current_provider = st.session_state.get("ai_provider_name", "Claude (Anthropic)")
# If current provider is Ollama but it's disabled, reset to Claude
if current_provider == "Ollama (Local)" and not OLLAMA_ENABLED:
    current_provider = "Claude (Anthropic)"

provider = st.selectbox(
    "Select AI Provider",
    options=ai_providers,
    index=ai_providers.index(current_provider) if current_provider in ai_providers else 0
)

# Provider-specific settings
saved_api_key = st.session_state.get("ai_api_key", "")
saved_model = st.session_state.get("ai_model", "")
saved_ollama_url = st.session_state.get("ollama_url", "http://localhost:11434")

if provider == "Claude (Anthropic)":
    default_key = saved_api_key if st.session_state.get("ai_provider") == "claude" else (ANTHROPIC_API_KEY or "")
    api_key = st.text_input(
        "Anthropic API Key",
        value=default_key,
        type="password",
        help="Get your API key from console.anthropic.com"
    )
    claude_models = ["claude-sonnet-4-20250514", "claude-3-5-haiku-20241022", "claude-3-opus-20240229"]
    default_model_idx = claude_models.index(saved_model) if saved_model in claude_models else 0
    model = st.selectbox(
        "Model",
        claude_models,
        index=default_model_idx
    )

    if st.button("Save & Test Connection", key="test_claude"):
        if api_key:
            with st.spinner("Testing connection..."):
                try:
                    import anthropic
                    client = anthropic.Anthropic(api_key=api_key)
                    response = client.messages.create(
                        model=model,
                        max_tokens=10,
                        messages=[{"role": "user", "content": "Hi"}]
                    )
                    # Save to session state
                    st.session_state.ai_provider = "claude"
                    st.session_state.ai_provider_name = provider
                    st.session_state.ai_api_key = api_key
                    st.session_state.ai_model = model
                    # Save to database for persistence (encrypt API key)
                    encrypted_key = encrypt_value(api_key)
                    db.save_settings_dict("ai", {
                        "provider": "claude",
                        "provider_name": provider,
                        "api_key": encrypted_key,
                        "model": model
                    })
                    st.toast("Connection successful! Settings saved.")
                except Exception as e:
                    st.error(f"Connection failed: {str(e)}")
        else:
            st.error("Please enter an API key")

elif provider == "OpenAI (GPT-5)":
    default_key = saved_api_key if st.session_state.get("ai_provider") == "openai" else (OPENAI_API_KEY or "")
    api_key = st.text_input(
        "OpenAI API Key",
        value=default_key,
        type="password",
        help="Get your API key from platform.openai.com"
    )
    openai_models = ["gpt-5-mini", "gpt-5-nano"]
    default_model_idx = openai_models.index(saved_model) if saved_model in openai_models else 0
    model = st.selectbox(
        "Model",
        openai_models,
        index=default_model_idx
    )

    if st.button("Save & Test Connection", key="test_openai"):
        if api_key:
            with st.spinner("Testing connection..."):
                try:
                    import openai
                    client = openai.OpenAI(api_key=api_key)
                    response = client.chat.completions.create(
                        model=model,
                        max_completion_tokens=10,
                        messages=[{"role": "user", "content": "Hi"}]
                    )
                    # Save to session state
                    st.session_state.ai_provider = "openai"
                    st.session_state.ai_provider_name = provider
                    st.session_state.ai_api_key = api_key
                    st.session_state.ai_model = model
                    # Save to database for persistence (encrypt API key)
                    encrypted_key = encrypt_value(api_key)
                    db.save_settings_dict("ai", {
                        "provider": "openai",
                        "provider_name": provider,
                        "api_key": encrypted_key,
                        "model": model
                    })
                    st.toast("Connection successful! Settings saved.")
                except Exception as e:
                    st.error(f"Connection failed: {str(e)}")
        else:
            st.error("Please enter an API key")

elif provider == "Ollama (Local)":
    ollama_url = st.text_input(
        "Ollama URL",
        value=saved_ollama_url if st.session_state.get("ai_provider") == "ollama" else "http://localhost:11434",
        help="URL where Ollama is running"
    )
    default_ollama_model = saved_model if st.session_state.get("ai_provider") == "ollama" else "llama3.2"
    model = st.text_input(
        "Model Name",
        value=default_ollama_model,
        help="Model must be pulled in Ollama first"
    )

    if st.button("Save & Test Connection", key="test_ollama"):
        with st.spinner("Testing connection..."):
            try:
                import ollama
                response = ollama.chat(
                    model=model,
                    messages=[{"role": "user", "content": "Hi"}]
                )
                # Save to session state
                st.session_state.ai_provider = "ollama"
                st.session_state.ai_provider_name = provider
                st.session_state.ai_model = model
                st.session_state.ollama_url = ollama_url
                # Save to database for persistence
                db.save_settings_dict("ai", {
                    "provider": "ollama",
                    "provider_name": provider,
                    "model": model,
                    "ollama_url": ollama_url
                })
                st.toast("Connection successful! Settings saved.")
            except Exception as e:
                st.error(f"Connection failed: {str(e)}")

else:
    st.markdown("""
    <div style="background: rgba(148, 163, 184, 0.1); border: 1px solid rgba(148, 163, 184, 0.2);
                border-radius: 12px; padding: 1rem; margin-top: 1rem;">
        <div style="color: #94A3B8; font-size: 0.875rem;">
            AI features will be disabled. You can still search for jobs and track applications.
        </div>
    </div>
    """, unsafe_allow_html=True)

    if st.button("Save Settings", key="save_none"):
        st.session_state.ai_provider = None
        st.session_state.ai_provider_name = "None (Disable AI)"
        st.session_state.ai_api_key = ""
        st.session_state.ai_model = ""
        # Save to database
        db.save_settings_dict("ai", {
            "provider": "",
            "provider_name": "None (Disable AI)",
            "api_key": "",
            "model": ""
        })
        st.toast("AI disabled. Settings saved.")

# Current AI status
if st.session_state.get("ai_provider"):
    st.markdown(f"""
    <div style="background: rgba(16, 185, 129, 0.08); border: 1px solid rgba(16, 185, 129, 0.2);
                border-radius: 12px; padding: 1rem; margin-top: 1rem;">
        <div style="display: flex; align-items: center; gap: 0.75rem;">
            <div style="width: 8px; height: 8px; border-radius: 50%; background: #10B981;"></div>
            <div style="color: #10B981; font-size: 0.875rem; font-weight: 600;">
                AI Enabled: {st.session_state.get('ai_provider_name', 'Unknown')}
                ({st.session_state.get('ai_model', 'Unknown')})
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# Location Management
st.markdown("<br>", unsafe_allow_html=True)
st.markdown(section_header("Saved Locations"), unsafe_allow_html=True)

st.markdown("""
<div style="color: #475569; font-size: 0.875rem; margin-bottom: 1.5rem;">
    Add universities or areas where you want to search for jobs
</div>
""", unsafe_allow_html=True)

locations = db.get_locations()

# Add new location
with st.expander("Add New Location", expanded=not locations):
    loc_name = st.text_input(
        "Location Name",
        placeholder="e.g., UC Berkeley, My Home"
    )
    loc_address = st.text_input(
        "Address",
        placeholder="e.g., UC Berkeley, Berkeley, CA"
    )
    loc_radius = st.slider(
        "Default Search Radius",
        min_value=1,
        max_value=50,
        value=DEFAULT_RADIUS_MILES,
        format="%d miles"
    )
    loc_default = st.checkbox("Set as default location", value=not locations)

    if st.button("📍 Add Location", type="primary"):
        if loc_name and loc_address:
            with st.spinner("Geocoding address..."):
                coords = geocode_address(loc_address)

            if coords:
                location = SavedLocation(
                    name=loc_name,
                    address=loc_address,
                    latitude=coords[0],
                    longitude=coords[1],
                    radius_miles=loc_radius,
                    is_default=loc_default
                )
                db.save_location(location)
                st.toast(f"Added {loc_name}")
                st.rerun()
            else:
                st.error("Could not geocode address. Please check and try again.")
        else:
            st.error("Please fill in both name and address")

# Display existing locations
if locations:
    st.markdown("<br>", unsafe_allow_html=True)

    for loc in locations:
        default_badge = "⭐ " if loc.is_default else ""

        st.markdown(f"""
        <div style="background: #FFFFFF; border: 1px solid #E2E8F0;
                    border-radius: 16px; padding: 1.25rem; margin-bottom: 1rem;">
            <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                <div>
                    <div style="font-family: 'Plus Jakarta Sans', sans-serif; font-weight: 700; color: #0F172A;
                                font-size: 1.125rem; margin-bottom: 0.25rem;">
                        {default_badge}{safe_html(loc.name)}
                    </div>
                    <div style="color: #475569; font-size: 0.875rem; margin-bottom: 0.5rem;">
                        {safe_html(loc.address)}
                    </div>
                    <div style="color: #94A3B8; font-size: 0.75rem;">
                        📍 {loc.latitude:.4f}, {loc.longitude:.4f} · 🔍 {loc.radius_miles} mi radius
                    </div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        col1, col2 = st.columns([1, 1])
        with col1:
            if not loc.is_default:
                if st.button("Set as Default", key=f"default_{loc.id}", use_container_width=True):
                    loc.is_default = True
                    db.save_location(loc)
                    st.rerun()
        with col2:
            if st.button("🗑️ Delete", key=f"delete_{loc.id}", use_container_width=True):
                db.delete_location(loc.id)
                st.toast(f"Deleted {loc.name}")
                st.rerun()

else:
    st.markdown(empty_state(
        "📍",
        "No locations saved",
        "Add your university or preferred search area to start finding jobs."
    ), unsafe_allow_html=True)

# University Job Board Configuration
st.markdown("<br>", unsafe_allow_html=True)
st.markdown(section_header("University Job Board"), unsafe_allow_html=True)

st.markdown("""
<div style="color: #475569; font-size: 0.875rem; margin-bottom: 1.5rem;">
    Connect your university's career center job board for campus-specific opportunities
</div>
""", unsafe_allow_html=True)

# Load existing config
uni_config = st.session_state.get("university_job_board", {})

with st.expander("Configure University Job Board", expanded=not uni_config.get("url")):
    uni_name = st.text_input(
        "University Name",
        value=uni_config.get("name", ""),
        placeholder="e.g., Binghamton University"
    )

    uni_url = st.text_input(
        "Job Board URL",
        value=uni_config.get("url", ""),
        placeholder="e.g., https://www.binghamton.edu/ccpd/hire-bing-postings.html",
        help="Enter your university's career center job board URL"
    )

    st.markdown("""
    <div style="background: rgba(8, 145, 178, 0.08); border: 1px solid rgba(8, 145, 178, 0.2);
                border-radius: 12px; padding: 1rem; margin: 1rem 0;">
        <div style="font-family: 'Plus Jakarta Sans', sans-serif; font-weight: 700; color: #0891B2;
                    margin-bottom: 0.5rem; font-size: 0.875rem;">
            💡 Authentication (Optional)
        </div>
        <div style="color: #475569; font-size: 0.8rem;">
            If your university uses Handshake or another system requiring login, you can provide
            your session cookie for authenticated access. Log into your job portal in a browser,
            then copy the cookie value.
        </div>
    </div>
    """, unsafe_allow_html=True)

    use_auth = st.checkbox(
        "Enable authentication",
        value=uni_config.get("use_auth", False),
        help="Check if your university job board requires login"
    )

    auth_cookie = ""
    if use_auth:
        auth_cookie = st.text_input(
            "Session Cookie",
            value=uni_config.get("auth_cookie", ""),
            type="password",
            placeholder="Paste your session cookie here",
            help="Usually named 'session', '_handshake_session', or similar"
        )

        st.markdown("""
        <details style="margin-top: 0.5rem;">
            <summary style="cursor: pointer; color: #0891B2; font-size: 0.8rem; font-weight: 600;">
                How to get your session cookie
            </summary>
            <div style="padding: 0.75rem; background: #F8FAFC; border-radius: 8px; margin-top: 0.5rem;
                        font-size: 0.75rem; color: #475569;">
                <ol style="margin: 0; padding-left: 1.25rem;">
                    <li>Log into your university job portal in Chrome/Firefox</li>
                    <li>Press F12 to open Developer Tools</li>
                    <li>Go to Application tab → Cookies</li>
                    <li>Find the session cookie (often named 'session' or contains 'handshake')</li>
                    <li>Copy the entire cookie value</li>
                </ol>
                <p style="margin: 0.5rem 0 0 0; font-style: italic;">
                    Note: Cookies expire, so you may need to update this periodically.
                </p>
            </div>
        </details>
        """, unsafe_allow_html=True)

    col1, col2 = st.columns([1, 1])

    with col1:
        if st.button("💾 Save University Config", type="primary", use_container_width=True):
            if uni_name and uni_url:
                uni_data = {
                    "name": uni_name,
                    "url": uni_url,
                    "use_auth": use_auth,
                    "auth_cookie": auth_cookie if use_auth else ""
                }
                # Save to session state
                st.session_state.university_job_board = uni_data
                # Save to database for persistence
                db.save_settings_dict("uni", uni_data)
                st.toast(f"Saved {uni_name} job board!")
                st.rerun()
            else:
                st.error("Please enter both university name and URL")

    with col2:
        if st.button("🔍 Test Connection", use_container_width=True):
            if uni_url:
                with st.spinner("Testing connection..."):
                    try:
                        from scrapers.university import UniversityJobBoardScraper
                        scraper = UniversityJobBoardScraper(
                            university_name=uni_name or "University",
                            job_board_url=uni_url
                        )
                        # Add auth cookie if provided
                        if use_auth and auth_cookie:
                            scraper.headers["Cookie"] = auth_cookie

                        jobs = scraper.search(query="", location="", max_results=5)
                        if jobs:
                            # Check if it's a redirect to Handshake or similar
                            if len(jobs) == 1 and ("handshake" in jobs[0].title.lower() or "Access " in jobs[0].title):
                                st.info(
                                    f"**Detected: {jobs[0].title}**\n\n"
                                    f"This university uses an external job portal. You can:\n"
                                    f"1. Visit [{jobs[0].url}]({jobs[0].url}) directly and log in\n"
                                    f"2. Enable authentication above and provide your session cookie\n\n"
                                    f"When searching, this will appear as a link to access the portal."
                                )
                            else:
                                st.success(f"Found {len(jobs)} jobs!")
                                for job in jobs[:3]:
                                    st.markdown(f"- **{job.title}** at {job.company}")
                        else:
                            st.warning(
                                "Connected but no jobs found. The site may:\n"
                                "- Use Handshake or another system requiring login\n"
                                "- Load jobs via JavaScript (not supported)\n"
                                "- Have no current postings"
                            )
                    except Exception as e:
                        import traceback
                        st.error(f"Connection failed: {str(e)}\n\n{traceback.format_exc()}")
            else:
                st.error("Please enter a job board URL")

# Show current config
if uni_config.get("url"):
    st.markdown(f"""
    <div style="background: rgba(16, 185, 129, 0.08); border: 1px solid rgba(16, 185, 129, 0.2);
                border-radius: 12px; padding: 1rem; margin-top: 1rem;">
        <div style="display: flex; align-items: center; gap: 0.75rem;">
            <div style="width: 8px; height: 8px; border-radius: 50%; background: #10B981;"></div>
            <div style="color: #10B981; font-size: 0.875rem; font-weight: 600;">
                University Job Board Configured: {safe_html(uni_config.get('name', 'Unknown'))}
            </div>
        </div>
        <div style="color: #475569; font-size: 0.75rem; margin-top: 0.5rem; margin-left: 1.25rem;">
            {safe_html(uni_config.get('url', ''))}
        </div>
    </div>
    """, unsafe_allow_html=True)

# Auto-Search Settings
st.markdown("<br>", unsafe_allow_html=True)
st.markdown(section_header("Auto-Search"), unsafe_allow_html=True)

st.markdown("""
<div style="color: #475569; font-size: 0.875rem; margin-bottom: 1rem;">
    Configure automatic job searches to run on a schedule.
</div>
""", unsafe_allow_html=True)

from data.models import SearchSchedule

schedule = db.get_search_schedule()
if not schedule:
    schedule = SearchSchedule()

col1, col2 = st.columns(2)

with col1:
    auto_enabled = st.toggle(
        "Enable Auto-Search",
        value=schedule.enabled,
        help="Automatically search for jobs on a schedule"
    )

    frequency = st.selectbox(
        "Search Frequency",
        options=["daily", "weekly"],
        index=0 if schedule.frequency == "daily" else 1,
        disabled=not auto_enabled
    )

with col2:
    time_pref = st.selectbox(
        "Preferred Time",
        options=["morning", "afternoon", "evening"],
        index=["morning", "afternoon", "evening"].index(schedule.time_preference) if schedule.time_preference in ["morning", "afternoon", "evening"] else 0,
        disabled=not auto_enabled
    )

    # Show last run info
    if schedule.last_run:
        st.markdown(f"""
        <div style="font-size: 0.75rem; color: #94A3B8; margin-top: 1rem;">
            Last run: {schedule.last_run.strftime('%b %d, %Y at %I:%M %p')}
        </div>
        """, unsafe_allow_html=True)

# Search configuration
if auto_enabled:
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("""
    <div style="font-family: 'Plus Jakarta Sans', sans-serif; font-size: 0.875rem; font-weight: 700;
                color: #0F172A; margin-bottom: 0.75rem;">Search Configuration</div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:
        search_query = st.text_input(
            "Search Keywords",
            value=schedule.search_query or "",
            placeholder="e.g., software intern, retail"
        )

        search_sources = st.multiselect(
            "Job Sources",
            options=["Indeed", "LinkedIn", "Glassdoor", "College Recruiter", "WayUp"],
            default=schedule.search_sources if schedule.search_sources else ["Indeed", "LinkedIn"]
        )

    with col2:
        # Location selector
        locations = db.get_locations()
        loc_names = [loc.name for loc in locations]
        if loc_names:
            current_loc_idx = 0
            if schedule.search_location_id:
                for i, loc in enumerate(locations):
                    if loc.id == schedule.search_location_id:
                        current_loc_idx = i
                        break
            selected_loc = st.selectbox(
                "Search Location",
                options=loc_names,
                index=current_loc_idx
            )
            selected_location_id = locations[loc_names.index(selected_loc)].id if selected_loc else None
        else:
            st.info("Add a location first")
            selected_location_id = None

        search_job_types = st.multiselect(
            "Job Types",
            options=["Part-time", "Full-time", "Internship", "Contract", "Temporary"],
            default=schedule.search_job_types if schedule.search_job_types else ["Part-time", "Internship"]
        )

if st.button("💾 Save Auto-Search Settings", use_container_width=True):
    schedule.enabled = auto_enabled
    schedule.frequency = frequency
    schedule.time_preference = time_pref
    if auto_enabled:
        schedule.search_query = search_query
        schedule.search_sources = search_sources
        schedule.search_location_id = selected_location_id
        schedule.search_job_types = search_job_types
    db.save_search_schedule(schedule)
    st.toast("Auto-search settings saved!")
    st.rerun()

# Notification Preferences
st.markdown("<br>", unsafe_allow_html=True)
st.markdown(section_header("Notifications"), unsafe_allow_html=True)

from data.models import NotificationPreferences

notif_prefs = db.get_notification_preferences()
if not notif_prefs:
    notif_prefs = NotificationPreferences()

col1, col2 = st.columns(2)

with col1:
    st.markdown("""
    <div style="font-family: 'Plus Jakarta Sans', sans-serif; font-size: 0.875rem; font-weight: 700;
                color: #0F172A; margin-bottom: 0.75rem;">In-App Notifications</div>
    """, unsafe_allow_html=True)

    notify_jobs = st.checkbox(
        "New job matches",
        value=notif_prefs.notify_new_jobs
    )

    notify_apps = st.checkbox(
        "Application updates",
        value=notif_prefs.notify_application_updates
    )

with col2:
    st.markdown("""
    <div style="font-family: 'Plus Jakarta Sans', sans-serif; font-size: 0.875rem; font-weight: 700;
                color: #0F172A; margin-bottom: 0.75rem;">Email Notifications</div>
    """, unsafe_allow_html=True)

    email_enabled = st.checkbox(
        "Enable email notifications",
        value=notif_prefs.email_enabled
    )

    if email_enabled:
        email_address = st.text_input(
            "Email Address",
            value=notif_prefs.email_address or "",
            placeholder="your@email.com"
        )

        digest_freq = st.selectbox(
            "Email Frequency",
            options=["instant", "daily", "weekly"],
            index=["instant", "daily", "weekly"].index(notif_prefs.digest_frequency) if notif_prefs.digest_frequency in ["instant", "daily", "weekly"] else 0
        )
    else:
        email_address = notif_prefs.email_address
        digest_freq = notif_prefs.digest_frequency

if st.button("💾 Save Notification Settings", use_container_width=True):
    notif_prefs.notify_new_jobs = notify_jobs
    notif_prefs.notify_application_updates = notify_apps
    notif_prefs.email_enabled = email_enabled
    if email_enabled:
        notif_prefs.email_address = email_address
        notif_prefs.digest_frequency = digest_freq
    db.save_notification_preferences(notif_prefs)
    st.toast("Notification settings saved!")
    st.rerun()

# Data Management
st.markdown("<br>", unsafe_allow_html=True)
st.markdown(section_header("Data Management"), unsafe_allow_html=True)

col1, col2 = st.columns(2)

with col1:
    st.markdown("""
    <div style="font-family: 'Plus Jakarta Sans', sans-serif; font-size: 0.875rem; font-weight: 700;
                color: #0F172A; margin-bottom: 0.75rem;">Export Data</div>
    """, unsafe_allow_html=True)

    if st.button("📥 Export Jobs to CSV", use_container_width=True):
        jobs = db.get_jobs(limit=10000)
        if jobs:
            import pandas as pd
            df = pd.DataFrame([j.model_dump() for j in jobs])
            csv = df.to_csv(index=False)
            st.download_button(
                "Download CSV",
                csv,
                "jobs.csv",
                "text/csv",
                use_container_width=True
            )
        else:
            st.info("No jobs to export")

with col2:
    st.markdown("""
    <div style="font-family: 'Plus Jakarta Sans', sans-serif; font-size: 0.875rem; font-weight: 700;
                color: #0F172A; margin-bottom: 0.75rem;">Clear Data</div>
    """, unsafe_allow_html=True)

    if st.button("🗑️ Clear Job Cache", use_container_width=True):
        from data.cache import clear_cache
        clear_cache()
        st.toast("Cache cleared!")

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; padding: 1rem; color: #94A3B8; font-size: 0.75rem;">
    <span style="font-family: 'Plus Jakarta Sans', sans-serif; font-weight: 700;">⚔️ SideQuest</span>
    v1.0 · Student Job Search Agent
</div>
""", unsafe_allow_html=True)
