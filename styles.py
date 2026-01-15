"""Custom styling for SideQuest - Student Job Search Agent."""

# Google Fonts import
FONTS = """
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=Nunito+Sans:ital,wght@0,400;0,500;0,600;0,700;1,400&display=swap');
"""

# Main theme CSS - Bright, modern theme
THEME_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=Nunito+Sans:ital,wght@0,400;0,500;0,600;0,700;1,400&display=swap');

:root {
    /* Core palette - Bright theme */
    --bg-primary: #F8FAFC;
    --bg-secondary: #FFFFFF;
    --bg-card: #FFFFFF;
    --bg-card-hover: #F1F5F9;
    --bg-accent: #EFF6FF;

    /* Primary accent - Vibrant teal/cyan */
    --accent-primary: #0891B2;
    --accent-primary-light: #22D3EE;
    --accent-primary-dark: #0E7490;

    /* Secondary accent - Warm coral */
    --accent-coral: #F97316;
    --accent-coral-light: #FB923C;

    /* Additional accents */
    --accent-indigo: #6366F1;
    --accent-emerald: #10B981;
    --accent-amber: #F59E0B;
    --accent-rose: #F43F5E;
    --accent-danger: #DC2626;
    --accent-danger-dark: #B91C1C;

    /* Text colors */
    --text-primary: #0F172A;
    --text-secondary: #475569;
    --text-muted: #94A3B8;

    /* Gradients */
    --gradient-primary: linear-gradient(135deg, #0891B2 0%, #22D3EE 100%);
    --gradient-coral: linear-gradient(135deg, #F97316 0%, #FB923C 100%);
    --gradient-indigo: linear-gradient(135deg, #4F46E5 0%, #818CF8 100%);
    --gradient-hero: linear-gradient(135deg, #EFF6FF 0%, #F0FDFA 50%, #FFF7ED 100%);
    --gradient-danger: linear-gradient(135deg, #DC2626 0%, #EF4444 100%);

    /* Shadows */
    --shadow-sm: 0 1px 2px rgba(0, 0, 0, 0.05);
    --shadow-card: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
    --shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
    --shadow-glow-primary: 0 0 30px rgba(8, 145, 178, 0.2);
    --shadow-glow-coral: 0 0 30px rgba(249, 115, 22, 0.2);

    /* Borders */
    --border-subtle: 1px solid #E2E8F0;
    --border-focus: 1px solid #0891B2;

    /* Radius */
    --radius-sm: 8px;
    --radius-md: 12px;
    --radius-lg: 16px;
    --radius-xl: 24px;

    /* Spacing system */
    --spacing-xs: 0.25rem;
    --spacing-sm: 0.5rem;
    --spacing-md: 1rem;
    --spacing-lg: 1.5rem;
    --spacing-xl: 2rem;
    --spacing-2xl: 3rem;
    --spacing-3xl: 4rem;
}

/* Base overrides */
.stApp {
    background: var(--bg-primary);
    background-image:
        radial-gradient(ellipse at 0% 0%, rgba(8, 145, 178, 0.05) 0%, transparent 50%),
        radial-gradient(ellipse at 100% 100%, rgba(249, 115, 22, 0.04) 0%, transparent 50%);
}

/* Hide default Streamlit elements */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}

/* Hide default Streamlit page navigation in sidebar */
[data-testid="stSidebarNav"] {
    display: none !important;
}

/* Custom top navigation bar */
.top-nav {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.75rem 1rem;
    background: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 16px;
    margin-bottom: 1.5rem;
    flex-wrap: wrap;
}

.top-nav-brand {
    font-family: 'Plus Jakarta Sans', sans-serif;
    font-size: 1.25rem;
    font-weight: 800;
    background: linear-gradient(135deg, #0891B2 0%, #22D3EE 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin-right: 1rem;
    white-space: nowrap;
}

.top-nav-links {
    display: flex;
    gap: 0.25rem;
    flex-wrap: wrap;
}

.top-nav-link {
    font-family: 'Plus Jakarta Sans', sans-serif;
    font-size: 0.875rem;
    font-weight: 600;
    color: #475569;
    text-decoration: none;
    padding: 0.5rem 1rem;
    border-radius: 10px;
    transition: all 0.15s ease;
    white-space: nowrap;
}

.top-nav-link:hover {
    background: rgba(8, 145, 178, 0.08);
    color: #0891B2;
}

.top-nav-link.active {
    background: rgba(8, 145, 178, 0.12);
    color: #0891B2;
}

/* Page link styling for navigation */
[data-testid="stPageLink"] {
    background: transparent !important;
    border: none !important;
}

[data-testid="stPageLink"] a {
    font-family: 'Plus Jakarta Sans', sans-serif !important;
    font-size: 0.8rem !important;
    font-weight: 600 !important;
    color: #475569 !important;
    text-decoration: none !important;
    padding: 0.5rem 0.75rem !important;
    border-radius: 10px !important;
    transition: all 0.15s ease !important;
    display: block !important;
    text-align: center !important;
    white-space: nowrap !important;
}

[data-testid="stPageLink"] a:hover {
    background: rgba(8, 145, 178, 0.08) !important;
    color: #0891B2 !important;
}

/* Main content area */
.main .block-container {
    padding: 2rem 3rem;
    max-width: 1400px;
}

/* Typography */
h1, h2, h3, h4, h5, h6 {
    font-family: 'Plus Jakarta Sans', sans-serif !important;
    color: var(--text-primary) !important;
    font-weight: 700 !important;
}

h1 {
    font-size: 2.5rem !important;
    letter-spacing: -0.025em !important;
}

/* Only apply gradient to main page titles, not all h1 */
.main > div > div > div > h1 {
    background: var(--gradient-primary);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}

p, .stMarkdown p {
    font-family: 'Nunito Sans', sans-serif !important;
    color: var(--text-secondary) !important;
}

label {
    font-family: 'Plus Jakarta Sans', sans-serif !important;
    color: var(--text-primary) !important;
}

/* Sidebar styling */
[data-testid="stSidebar"] {
    background: var(--bg-secondary) !important;
    border-right: var(--border-subtle) !important;
}

[data-testid="stSidebar"] .stMarkdown h1,
[data-testid="stSidebar"] .stMarkdown h2,
[data-testid="stSidebar"] .stMarkdown h3 {
    font-size: 0.875rem !important;
    color: var(--text-muted) !important;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    margin-top: 1.5rem;
}

/* Buttons - Primary - Force all properties */
.stButton button,
.stButton > button,
.stButton button[kind="primary"],
[data-testid="stButton"] button,
[data-testid="baseButton-primary"],
button[data-testid="baseButton-primary"],
.stButton button p,
.stButton > button p,
.stButton button span,
.stButton > button span {
    font-family: 'Plus Jakarta Sans', sans-serif !important;
    font-weight: 600 !important;
    background: #0891B2 !important;
    background-color: #0891B2 !important;
    background-image: none !important;
    color: #FFFFFF !important;
    -webkit-text-fill-color: #FFFFFF !important;
    border: none !important;
    border-radius: 10px !important;
    padding: 0.625rem 1.25rem !important;
    transition: all 0.15s ease !important;
    box-shadow: 0 1px 3px rgba(8, 145, 178, 0.3) !important;
    text-shadow: none !important;
}

/* Button text specifically */
.stButton button p,
.stButton button span,
.stButton button div {
    background: transparent !important;
    background-color: transparent !important;
    color: #FFFFFF !important;
    -webkit-text-fill-color: #FFFFFF !important;
}

.stButton button:hover,
[data-testid="stButton"] button:hover,
[data-testid="baseButton-primary"]:hover {
    background: #0E7490 !important;
    background-color: #0E7490 !important;
    color: #FFFFFF !important;
    -webkit-text-fill-color: #FFFFFF !important;
    transform: translateY(-1px) !important;
    box-shadow: 0 4px 12px rgba(8, 145, 178, 0.35) !important;
}

.stButton button:active,
[data-testid="stButton"] button:active {
    transform: translateY(0) !important;
    box-shadow: 0 1px 2px rgba(8, 145, 178, 0.2) !important;
}

.stButton button:focus,
[data-testid="stButton"] button:focus {
    outline: none !important;
    box-shadow: 0 0 0 3px rgba(8, 145, 178, 0.2) !important;
}

/* Secondary/default button style - only target explicitly secondary buttons */
.stButton button[kind="secondary"],
[data-testid="baseButton-secondary"] {
    background: #FFFFFF !important;
    background-color: #FFFFFF !important;
    border: 2px solid #0891B2 !important;
    color: #0891B2 !important;
    -webkit-text-fill-color: #0891B2 !important;
    box-shadow: none !important;
}

.stButton button[kind="secondary"] p,
.stButton button[kind="secondary"] span,
[data-testid="baseButton-secondary"] p,
[data-testid="baseButton-secondary"] span {
    background: transparent !important;
    background-color: transparent !important;
    color: #0891B2 !important;
    -webkit-text-fill-color: #0891B2 !important;
}

.stButton button[kind="secondary"]:hover,
[data-testid="baseButton-secondary"]:hover {
    background: rgba(8, 145, 178, 0.1) !important;
    background-color: rgba(8, 145, 178, 0.1) !important;
    border-color: #0891B2 !important;
    color: #0891B2 !important;
    -webkit-text-fill-color: #0891B2 !important;
}

/* Primary buttons - highest specificity to ensure they stay teal with white text */
.stButton button[kind="primary"],
[data-testid="baseButton-primary"],
[data-testid="stSidebar"] .stButton button[kind="primary"],
[data-testid="stSidebar"] [data-testid="baseButton-primary"] {
    background: #0891B2 !important;
    background-color: #0891B2 !important;
    border: none !important;
    color: #FFFFFF !important;
    -webkit-text-fill-color: #FFFFFF !important;
    display: inline-flex !important;
    visibility: visible !important;
    opacity: 1 !important;
}

.stButton button[kind="primary"] p,
.stButton button[kind="primary"] span,
[data-testid="baseButton-primary"] p,
[data-testid="baseButton-primary"] span {
    color: #FFFFFF !important;
    -webkit-text-fill-color: #FFFFFF !important;
    background: transparent !important;
}

/* Ensure sidebar buttons are always visible */
[data-testid="stSidebar"] .stButton {
    display: block !important;
    visibility: visible !important;
    opacity: 1 !important;
}

[data-testid="stSidebar"] .stButton button {
    display: inline-flex !important;
    visibility: visible !important;
    opacity: 1 !important;
    width: 100% !important;
}

/* Input fields */
.stTextInput > div > div > input,
.stTextArea > div > div > textarea {
    font-family: 'Nunito Sans', sans-serif !important;
    background: #FFFFFF !important;
    border: 1px solid #E2E8F0 !important;
    border-radius: 12px !important;
    color: #0F172A !important;
    padding: 0.75rem 1rem !important;
}

.stTextInput > div > div > input:focus,
.stTextArea > div > div > textarea:focus {
    border-color: #0891B2 !important;
    box-shadow: 0 0 0 3px rgba(8, 145, 178, 0.15) !important;
}

/* Selectbox styling */
[data-testid="stSelectbox"] {
    background: transparent !important;
}

[data-testid="stSelectbox"] > div > div {
    background: #FFFFFF !important;
    border: 1px solid #E2E8F0 !important;
    border-radius: 12px !important;
}

[data-testid="stSelectbox"] > div > div > div {
    font-family: 'Nunito Sans', sans-serif !important;
    color: #0F172A !important;
    min-height: auto !important;
    padding: 0.5rem 0.75rem !important;
}

/* Selectbox dropdown menu */
[data-baseweb="popover"] {
    background: #FFFFFF !important;
    border: 1px solid #E2E8F0 !important;
    border-radius: 12px !important;
    box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05) !important;
    overflow: hidden !important;
}

[data-baseweb="menu"] {
    background: #FFFFFF !important;
}

[data-baseweb="menu"] li {
    font-family: 'Nunito Sans', sans-serif !important;
    color: #0F172A !important;
    padding: 0.75rem 1rem !important;
}

[data-baseweb="menu"] li:hover {
    background: #F1F5F9 !important;
}

/* Selected option in dropdown */
[data-baseweb="menu"] li[aria-selected="true"] {
    background: rgba(8, 145, 178, 0.1) !important;
    color: #0891B2 !important;
}

/* Multiselect styling */
[data-testid="stMultiSelect"] > div > div {
    background: #FFFFFF !important;
    border: 1px solid #E2E8F0 !important;
    border-radius: 12px !important;
}

[data-testid="stMultiSelect"] span[data-baseweb="tag"] {
    background: rgba(8, 145, 178, 0.1) !important;
    border: 1px solid rgba(8, 145, 178, 0.2) !important;
    color: #0891B2 !important;
    border-radius: 8px !important;
}

/* Radio buttons */
[data-testid="stRadio"] > div {
    gap: 0.5rem !important;
}

[data-testid="stRadio"] label {
    font-family: 'Nunito Sans', sans-serif !important;
    background: #FFFFFF !important;
    border: 1px solid #E2E8F0 !important;
    border-radius: 8px !important;
    padding: 0.5rem 1rem !important;
    transition: all 0.2s ease !important;
}

[data-testid="stRadio"] label:hover {
    border-color: #0891B2 !important;
}

[data-testid="stRadio"] label[data-checked="true"] {
    background: rgba(8, 145, 178, 0.1) !important;
    border-color: #0891B2 !important;
    color: #0891B2 !important;
}

/* Number input styling */
[data-testid="stNumberInput"] > div > div > input {
    font-family: 'Nunito Sans', sans-serif !important;
    background: #FFFFFF !important;
    border: 1px solid #E2E8F0 !important;
    border-radius: 12px !important;
    color: #0F172A !important;
}

[data-testid="stNumberInput"] button {
    background: #F8FAFC !important;
    border: 1px solid #E2E8F0 !important;
    color: #475569 !important;
}

[data-testid="stNumberInput"] button:hover {
    background: #EFF6FF !important;
    border-color: #0891B2 !important;
    color: #0891B2 !important;
}

/* Time input styling */
[data-testid="stTimeInput"] > div > div > input {
    font-family: 'Nunito Sans', sans-serif !important;
    background: #FFFFFF !important;
    border: 1px solid #E2E8F0 !important;
    border-radius: 12px !important;
    color: #0F172A !important;
}

/* Date input styling */
[data-testid="stDateInput"] > div > div > input {
    font-family: 'Nunito Sans', sans-serif !important;
    background: #FFFFFF !important;
    border: 1px solid #E2E8F0 !important;
    border-radius: 12px !important;
    color: #0F172A !important;
}

/* Slider styling */
[data-testid="stSlider"] [data-baseweb="slider"] {
    background: transparent !important;
}

/* Slider track (background) */
[data-testid="stSlider"] [data-baseweb="slider"] > div {
    background: #E2E8F0 !important;
}

/* Slider filled track */
[data-testid="stSlider"] [data-baseweb="slider"] > div > div,
[data-testid="stSlider"] [data-baseweb="slider"] > div > div[role="progressbar"] {
    background: #0891B2 !important;
    background-color: #0891B2 !important;
}

/* Slider thumb/handle */
[data-testid="stSlider"] [data-baseweb="slider"] [role="slider"],
[data-testid="stSlider"] [data-baseweb="slider"] > div > div:last-child {
    background: #0891B2 !important;
    background-color: #0891B2 !important;
    border: 2px solid #FFFFFF !important;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.15) !important;
}

/* Slider value text */
[data-testid="stSlider"] [data-testid="stTickBarMin"],
[data-testid="stSlider"] [data-testid="stTickBarMax"],
[data-testid="stSlider"] > div > div > div > div:last-child {
    color: #0891B2 !important;
    -webkit-text-fill-color: #0891B2 !important;
    font-family: 'Nunito Sans', sans-serif !important;
    font-weight: 600 !important;
}

/* Checkbox styling */
[data-testid="stCheckbox"] > label > span:first-child {
    background: #FFFFFF !important;
    border: 2px solid #E2E8F0 !important;
    border-radius: 6px !important;
}

[data-testid="stCheckbox"] > label > span:first-child[aria-checked="true"] {
    background: #0891B2 !important;
    border-color: #0891B2 !important;
}

/* Progress bar */
.stProgress > div > div > div > div {
    background: linear-gradient(135deg, #0891B2 0%, #22D3EE 100%) !important;
}

/* Spinner */
.stSpinner > div {
    border-color: #0891B2 transparent transparent transparent !important;
}

/* Toast messages */
[data-testid="stToast"] {
    background: #FFFFFF !important;
    border: 1px solid #E2E8F0 !important;
    border-radius: 12px !important;
    box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05) !important;
}

/* File uploader */
[data-testid="stFileUploader"] > div {
    background: #FFFFFF !important;
    border: 2px dashed #E2E8F0 !important;
    border-radius: 12px !important;
}

[data-testid="stFileUploader"] > div:hover {
    border-color: #0891B2 !important;
}

/* Labels for inputs */
.stTextInput label,
.stTextArea label,
.stSelectbox label,
.stMultiSelect label,
.stNumberInput label,
.stDateInput label,
.stTimeInput label,
.stSlider label {
    font-family: 'Plus Jakarta Sans', sans-serif !important;
    font-weight: 600 !important;
    color: #0F172A !important;
    font-size: 0.875rem !important;
}

/* Help text */
.stTextInput small,
.stTextArea small,
.stSelectbox small,
[data-testid="stWidgetLabel"] + small {
    font-family: 'Nunito Sans', sans-serif !important;
    color: #94A3B8 !important;
    font-size: 0.75rem !important;
}

/* Metrics */
[data-testid="stMetric"] {
    background: var(--bg-card) !important;
    border: var(--border-subtle) !important;
    border-radius: var(--radius-lg) !important;
    padding: 1.5rem !important;
}

[data-testid="stMetricLabel"] {
    font-family: 'Plus Jakarta Sans', sans-serif !important;
    font-size: 0.75rem !important;
    text-transform: uppercase !important;
    letter-spacing: 0.05em !important;
    color: var(--text-muted) !important;
}

[data-testid="stMetricValue"] {
    font-family: 'Plus Jakarta Sans', sans-serif !important;
    font-size: 2rem !important;
    font-weight: 700 !important;
    color: var(--text-primary) !important;
}

/* Expanders - minimal styling */
[data-testid="stExpander"] {
    border: 1px solid #E2E8F0 !important;
    border-radius: 12px !important;
}

[data-testid="stExpander"] [data-testid="stExpanderDetails"] {
    background: #FFFFFF !important;
}

/* Hide icon text that shouldn't be visible */
[data-testid="stExpander"] svg + span,
[data-testid="stExpander"] [data-testid="stIconMaterial"],
.material-symbols-rounded,
span[class*="icon"],
[data-testid="stExpander"] summary > div > span:first-child {
    font-size: 0 !important;
    width: 24px !important;
    height: 24px !important;
    overflow: hidden !important;
}

/* Ensure expander toggle icon displays correctly */
[data-testid="stExpander"] summary svg {
    width: 24px !important;
    height: 24px !important;
    min-width: 24px !important;
}

/* Tabs */
.stTabs [data-baseweb="tab-list"] {
    gap: 0.25rem;
    background: var(--bg-accent) !important;
    padding: 0.375rem !important;
    border-radius: var(--radius-lg) !important;
}

.stTabs [data-baseweb="tab"] {
    font-family: 'Plus Jakarta Sans', sans-serif !important;
    font-weight: 600 !important;
    color: var(--text-muted) !important;
    background: transparent !important;
    border-radius: var(--radius-md) !important;
    padding: 0.625rem 1rem !important;
}

.stTabs [aria-selected="true"] {
    background: var(--bg-secondary) !important;
    color: var(--accent-primary) !important;
    box-shadow: var(--shadow-sm) !important;
}

/* Sliders */
.stSlider > div > div > div > div {
    background: var(--accent-primary) !important;
}

/* Checkboxes */
.stCheckbox > label > span {
    color: var(--text-secondary) !important;
}

/* Success/Info/Warning/Error messages */
.stSuccess {
    background: rgba(16, 185, 129, 0.1) !important;
    border: 1px solid var(--accent-emerald) !important;
    border-radius: var(--radius-md) !important;
    color: var(--accent-emerald) !important;
}

.stInfo {
    background: rgba(8, 145, 178, 0.1) !important;
    border: 1px solid var(--accent-primary) !important;
    border-radius: var(--radius-md) !important;
    color: var(--accent-primary) !important;
}

.stWarning {
    background: rgba(245, 158, 11, 0.1) !important;
    border: 1px solid var(--accent-amber) !important;
    border-radius: var(--radius-md) !important;
    color: var(--accent-amber) !important;
}

.stError {
    background: rgba(244, 63, 94, 0.1) !important;
    border: 1px solid var(--accent-rose) !important;
    border-radius: var(--radius-md) !important;
    color: var(--accent-rose) !important;
}

/* Dividers */
hr {
    border: none !important;
    height: 1px !important;
    background: linear-gradient(90deg, transparent, var(--accent-primary), transparent) !important;
    margin: 2rem 0 !important;
}

/* Links */
a {
    color: var(--accent-primary) !important;
    text-decoration: none !important;
    transition: color 0.2s ease !important;
}

a:hover {
    color: var(--accent-primary-dark) !important;
}

/* Scrollbar */
::-webkit-scrollbar {
    width: 8px;
    height: 8px;
}

::-webkit-scrollbar-track {
    background: var(--bg-primary);
}

::-webkit-scrollbar-thumb {
    background: #CBD5E1;
    border-radius: 4px;
}

::-webkit-scrollbar-thumb:hover {
    background: var(--accent-primary);
}

/* Animations */
@keyframes fadeInUp {
    from {
        opacity: 0;
        transform: translateY(20px);
    }
    to {
        opacity: 1;
        transform: translateY(0);
    }
}

@keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.6; }
}

@keyframes shimmer {
    0% { background-position: -200% 0; }
    100% { background-position: 200% 0; }
}

.animate-fade-in {
    animation: fadeInUp 0.5s ease-out forwards;
}

.animate-pulse {
    animation: pulse 2s ease-in-out infinite;
}

/* ========================================
   MOBILE RESPONSIVENESS
   ======================================== */

/* Tablet breakpoint */
@media (max-width: 768px) {
    .main .block-container {
        padding: 1rem 1.5rem !important;
    }

    h1 {
        font-size: 1.75rem !important;
    }

    /* Top navigation responsive */
    .top-nav {
        padding: 0.5rem 0.75rem;
        gap: 0.25rem;
    }

    .top-nav-brand {
        font-size: 1rem;
        margin-right: 0.5rem;
    }

    .top-nav-link {
        font-size: 0.75rem;
        padding: 0.375rem 0.5rem;
    }

    [data-testid="stPageLink"] a {
        font-size: 0.7rem !important;
        padding: 0.375rem 0.5rem !important;
    }

    /* Hero section responsive */
    .hero-section {
        padding: 1.5rem;
    }

    .hero-title {
        font-size: 1.5rem;
    }

    .hero-subtitle {
        font-size: 0.9375rem;
    }

    /* Stat cards responsive */
    .stat-card {
        padding: 1.25rem;
    }

    .stat-value {
        font-size: 2rem;
    }

    /* Pipeline responsive - horizontal scroll */
    .pipeline-container {
        gap: 0.5rem;
    }

    .pipeline-stage {
        min-width: 100px;
        padding: 1rem;
    }

    .pipeline-count {
        font-size: 1.5rem;
    }

    /* Job cards responsive */
    .job-card {
        padding: 1rem;
    }

    .job-card-title {
        font-size: 1rem;
    }

    .job-card-meta {
        gap: 0.375rem;
    }

    .job-tag {
        font-size: 0.6875rem;
        padding: 0.25rem 0.5rem;
    }

    /* Feature cards responsive */
    .feature-card {
        padding: 1.25rem;
    }

    .feature-icon {
        width: 40px;
        height: 40px;
        font-size: 1.25rem;
    }

    /* Section headers */
    .section-header {
        margin: 1.5rem 0 1rem 0;
    }

    .section-title {
        font-size: 1.125rem;
    }
}

/* Mobile breakpoint */
@media (max-width: 480px) {
    .main .block-container {
        padding: 0.75rem 1rem !important;
    }

    h1 {
        font-size: 1.5rem !important;
    }

    /* Top nav mobile - wrap and center */
    .top-nav {
        flex-direction: column;
        align-items: center;
        text-align: center;
    }

    .top-nav-brand {
        margin-right: 0;
        margin-bottom: 0.5rem;
    }

    .top-nav-links {
        justify-content: center;
    }

    .top-nav-link {
        font-size: 0.6875rem;
        padding: 0.375rem 0.5rem;
    }

    [data-testid="stPageLink"] a {
        font-size: 0.65rem !important;
        padding: 0.3rem 0.4rem !important;
    }

    /* Hero mobile */
    .hero-section {
        padding: 1.25rem;
        margin-bottom: 1rem;
    }

    .hero-title {
        font-size: 1.25rem;
    }

    .hero-subtitle {
        font-size: 0.875rem;
    }

    /* Stats mobile */
    .stat-card {
        padding: 1rem;
    }

    .stat-value {
        font-size: 1.75rem;
    }

    .stat-label {
        font-size: 0.625rem;
    }

    /* Pipeline mobile */
    .pipeline-stage {
        min-width: 85px;
        padding: 0.75rem;
    }

    .pipeline-count {
        font-size: 1.25rem;
    }

    .pipeline-label {
        font-size: 0.625rem;
    }

    /* Job cards mobile */
    .job-card {
        padding: 0.875rem;
        margin-bottom: 0.75rem;
    }

    .job-card-title {
        font-size: 0.9375rem;
    }

    .job-card-company {
        font-size: 0.8125rem;
    }

    /* Empty state mobile */
    .empty-state {
        padding: 2rem 1.5rem;
    }

    .empty-state-icon {
        font-size: 2.5rem;
    }

    .empty-state-title {
        font-size: 1rem;
    }

    /* Buttons - ensure touch targets are at least 44px */
    .stButton button {
        min-height: 44px !important;
        padding: 0.75rem 1rem !important;
    }

    /* Form inputs - larger touch targets */
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea {
        min-height: 44px !important;
        padding: 0.875rem 1rem !important;
    }
}

/* Small mobile breakpoint */
@media (max-width: 375px) {
    .main .block-container {
        padding: 0.5rem 0.75rem !important;
    }

    .top-nav-link {
        font-size: 0.625rem;
        padding: 0.25rem 0.375rem;
    }

    [data-testid="stPageLink"] a {
        font-size: 0.6rem !important;
        padding: 0.25rem 0.35rem !important;
    }

    .job-card-meta {
        flex-direction: column;
        align-items: flex-start;
    }
}

/* ========================================
   SKELETON LOADERS & LOADING STATES
   ======================================== */

/* Skeleton base */
.skeleton {
    background: linear-gradient(
        90deg,
        #E2E8F0 0%,
        #F1F5F9 50%,
        #E2E8F0 100%
    );
    background-size: 200% 100%;
    animation: shimmer 1.5s ease-in-out infinite;
    border-radius: var(--radius-sm);
}

/* Skeleton job card */
.skeleton-job-card {
    background: var(--bg-card);
    border: var(--border-subtle);
    border-radius: var(--radius-lg);
    padding: 1.5rem;
    margin-bottom: 1rem;
}

.skeleton-title {
    height: 1.25rem;
    width: 60%;
    margin-bottom: 0.75rem;
}

.skeleton-company {
    height: 1rem;
    width: 45%;
    margin-bottom: 1rem;
}

.skeleton-tags {
    display: flex;
    gap: 0.5rem;
}

.skeleton-tag {
    height: 1.5rem;
    width: 80px;
    border-radius: 100px;
}

/* Skeleton stat card */
.skeleton-stat-card {
    background: var(--bg-card);
    border: var(--border-subtle);
    border-radius: var(--radius-xl);
    padding: 1.75rem;
    text-align: center;
}

.skeleton-stat-value {
    height: 2.5rem;
    width: 60%;
    margin: 0 auto 0.5rem auto;
}

.skeleton-stat-label {
    height: 0.75rem;
    width: 80%;
    margin: 0 auto;
}

/* Loading spinner overlay */
.loading-overlay {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(248, 250, 252, 0.8);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 9999;
    backdrop-filter: blur(4px);
}

.loading-spinner {
    width: 48px;
    height: 48px;
    border: 4px solid #E2E8F0;
    border-top-color: var(--accent-primary);
    border-radius: 50%;
    animation: spin 0.8s linear infinite;
}

@keyframes spin {
    to { transform: rotate(360deg); }
}

/* Loading button state */
.btn-loading {
    position: relative;
    pointer-events: none;
    opacity: 0.7;
}

.btn-loading::after {
    content: '';
    position: absolute;
    width: 16px;
    height: 16px;
    top: 50%;
    left: 50%;
    margin-top: -8px;
    margin-left: -8px;
    border: 2px solid transparent;
    border-top-color: currentColor;
    border-radius: 50%;
    animation: spin 0.6s linear infinite;
}

/* ========================================
   BUTTON VARIANTS & FORM STATES
   ======================================== */

/* Danger/Delete button */
.btn-danger,
.stButton button.btn-danger,
[data-testid="stButton"] button.btn-danger {
    background: var(--accent-danger) !important;
    background-color: var(--accent-danger) !important;
    color: #FFFFFF !important;
    border: none !important;
}

.btn-danger:hover,
.stButton button.btn-danger:hover,
[data-testid="stButton"] button.btn-danger:hover {
    background: var(--accent-danger-dark) !important;
    background-color: var(--accent-danger-dark) !important;
    box-shadow: 0 4px 12px rgba(220, 38, 38, 0.35) !important;
}

/* Ghost/Subtle button */
.btn-ghost {
    background: transparent !important;
    color: var(--text-secondary) !important;
    border: none !important;
    box-shadow: none !important;
}

.btn-ghost:hover {
    background: var(--bg-card-hover) !important;
    color: var(--text-primary) !important;
}

/* Small button variant */
.btn-sm {
    padding: 0.375rem 0.75rem !important;
    font-size: 0.75rem !important;
    min-height: auto !important;
}

/* Disabled state */
.stButton button:disabled,
[data-testid="stButton"] button:disabled {
    opacity: 0.5 !important;
    cursor: not-allowed !important;
    transform: none !important;
}

/* Form validation states */
.stTextInput.error > div > div > input,
.stTextArea.error > div > div > textarea {
    border-color: var(--accent-danger) !important;
    box-shadow: 0 0 0 3px rgba(220, 38, 38, 0.15) !important;
}

.stTextInput.success > div > div > input,
.stTextArea.success > div > div > textarea {
    border-color: var(--accent-emerald) !important;
    box-shadow: 0 0 0 3px rgba(16, 185, 129, 0.15) !important;
}

/* Required field indicator */
.required-field::after {
    content: ' *';
    color: var(--accent-danger);
    font-weight: 600;
}

/* Helper/error text */
.field-error {
    font-family: 'Nunito Sans', sans-serif;
    font-size: 0.75rem;
    color: var(--accent-danger);
    margin-top: 0.25rem;
}

.field-hint {
    font-family: 'Nunito Sans', sans-serif;
    font-size: 0.75rem;
    color: var(--text-muted);
    margin-top: 0.25rem;
}

/* ========================================
   ACCESSIBILITY IMPROVEMENTS
   ======================================== */

/* Focus indicators for keyboard navigation */
*:focus-visible {
    outline: 2px solid var(--accent-primary) !important;
    outline-offset: 2px !important;
}

.stButton button:focus-visible,
[data-testid="stButton"] button:focus-visible {
    outline: 2px solid var(--accent-primary) !important;
    outline-offset: 2px !important;
    box-shadow: 0 0 0 4px rgba(8, 145, 178, 0.2) !important;
}

/* Input focus visible */
.stTextInput > div > div > input:focus-visible,
.stTextArea > div > div > textarea:focus-visible,
[data-testid="stSelectbox"] > div > div:focus-within {
    outline: 2px solid var(--accent-primary) !important;
    outline-offset: 1px !important;
}

/* Link focus */
a:focus-visible {
    outline: 2px solid var(--accent-primary) !important;
    outline-offset: 2px !important;
    border-radius: 2px;
}

/* Skip link for screen readers */
.skip-link {
    position: absolute;
    top: -40px;
    left: 0;
    background: var(--accent-primary);
    color: white;
    padding: 0.5rem 1rem;
    z-index: 10000;
    transition: top 0.2s ease;
}

.skip-link:focus {
    top: 0;
}

/* Reduced motion preference */
@media (prefers-reduced-motion: reduce) {
    *,
    *::before,
    *::after {
        animation-duration: 0.01ms !important;
        animation-iteration-count: 1 !important;
        transition-duration: 0.01ms !important;
    }

    .skeleton {
        animation: none;
        background: #E2E8F0;
    }
}

/* High contrast mode support */
@media (prefers-contrast: high) {
    .job-card {
        border-width: 2px;
    }

    .stButton button {
        border: 2px solid currentColor !important;
    }

    .job-tag {
        border-width: 2px;
    }
}

/* Screen reader only utility */
.sr-only {
    position: absolute;
    width: 1px;
    height: 1px;
    padding: 0;
    margin: -1px;
    overflow: hidden;
    clip: rect(0, 0, 0, 0);
    white-space: nowrap;
    border: 0;
}
</style>
"""

# Custom component styles
CARD_STYLES = """
<style>
.job-card {
    background: var(--bg-card);
    border: var(--border-subtle);
    border-radius: var(--radius-lg);
    padding: 1.5rem;
    margin-bottom: 1rem;
    transition: all 0.2s ease;
    position: relative;
    overflow: hidden;
}

.job-card::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    width: 4px;
    height: 100%;
    background: var(--gradient-primary);
    opacity: 0;
    transition: opacity 0.2s ease;
}

.job-card:hover {
    transform: translateY(-2px);
    box-shadow: var(--shadow-lg);
    border-color: var(--accent-primary);
}

.job-card:hover::before {
    opacity: 1;
}

.job-card-title {
    font-family: 'Plus Jakarta Sans', sans-serif;
    font-size: 1.125rem;
    font-weight: 700;
    color: var(--text-primary);
    margin-bottom: 0.375rem;
}

.job-card-company {
    font-family: 'Nunito Sans', sans-serif;
    font-size: 0.9375rem;
    color: var(--accent-primary);
    font-weight: 600;
    margin-bottom: 0.75rem;
}

.job-card-meta {
    display: flex;
    flex-wrap: wrap;
    gap: 0.5rem;
    margin-bottom: 0;
}

.job-tag {
    font-family: 'Nunito Sans', sans-serif;
    font-size: 0.75rem;
    font-weight: 600;
    padding: 0.3rem 0.75rem;
    border-radius: 100px;
    background: var(--bg-accent);
    color: var(--accent-primary);
    border: 1px solid rgba(8, 145, 178, 0.2);
}

.job-tag.salary {
    background: rgba(16, 185, 129, 0.1);
    color: var(--accent-emerald);
    border-color: rgba(16, 185, 129, 0.2);
}

.job-tag.match {
    background: rgba(249, 115, 22, 0.1);
    color: var(--accent-coral);
    border-color: rgba(249, 115, 22, 0.2);
}

.job-tag.schedule-ok {
    background: rgba(16, 185, 129, 0.1);
    color: var(--accent-emerald);
    border-color: rgba(16, 185, 129, 0.2);
}

.job-tag.schedule-conflict {
    background: rgba(245, 158, 11, 0.1);
    color: var(--accent-amber);
    border-color: rgba(245, 158, 11, 0.2);
}

.job-tag.source-indeed {
    background: rgba(37, 99, 235, 0.1);
    color: #2563EB;
    border-color: rgba(37, 99, 235, 0.2);
}

.job-tag.source-linkedin {
    background: rgba(0, 119, 181, 0.1);
    color: #0077B5;
    border-color: rgba(0, 119, 181, 0.2);
}

.job-tag.source-glassdoor {
    background: rgba(12, 170, 65, 0.1);
    color: #0CAA41;
    border-color: rgba(12, 170, 65, 0.2);
}

.match-score-badge {
    display: inline-flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.5rem 1rem;
    background: var(--gradient-coral);
    border-radius: var(--radius-md);
    font-family: 'Plus Jakarta Sans', sans-serif;
    font-weight: 700;
    font-size: 0.875rem;
    color: white;
}

/* Stats cards */
.stat-card {
    background: var(--bg-card);
    border: var(--border-subtle);
    border-radius: var(--radius-xl);
    padding: 1.75rem;
    text-align: center;
    transition: all 0.2s ease;
}

.stat-card:hover {
    transform: translateY(-2px);
    box-shadow: var(--shadow-lg);
}

.stat-card.coral {
    border-color: rgba(249, 115, 22, 0.3);
    background: linear-gradient(135deg, #FFF7ED 0%, #FFFFFF 100%);
}

.stat-card.coral:hover {
    box-shadow: var(--shadow-glow-coral);
}

.stat-value {
    font-family: 'Plus Jakarta Sans', sans-serif;
    font-size: 2.5rem;
    font-weight: 800;
    background: var(--gradient-primary);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    line-height: 1;
    margin-bottom: 0.5rem;
}

.stat-value.coral {
    background: var(--gradient-coral);
    -webkit-background-clip: text;
    background-clip: text;
}

.stat-label {
    font-family: 'Plus Jakarta Sans', sans-serif;
    font-size: 0.6875rem;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: var(--text-muted);
    font-weight: 600;
}

/* Hero section */
.hero-section {
    background: var(--gradient-hero);
    border: var(--border-subtle);
    border-radius: var(--radius-xl);
    padding: 2.5rem;
    margin-bottom: 2rem;
    position: relative;
    overflow: hidden;
}

.hero-section::before {
    content: '';
    position: absolute;
    top: -30%;
    right: -10%;
    width: 40%;
    height: 160%;
    background: radial-gradient(ellipse, rgba(8, 145, 178, 0.08) 0%, transparent 60%);
    pointer-events: none;
}

.hero-section::after {
    content: '';
    position: absolute;
    bottom: -30%;
    left: -10%;
    width: 40%;
    height: 160%;
    background: radial-gradient(ellipse, rgba(249, 115, 22, 0.06) 0%, transparent 60%);
    pointer-events: none;
}

.hero-title {
    font-family: 'Plus Jakarta Sans', sans-serif;
    font-size: 2rem;
    font-weight: 800;
    color: var(--text-primary);
    margin-bottom: 0.5rem;
    position: relative;
}

.hero-subtitle {
    font-family: 'Nunito Sans', sans-serif;
    font-size: 1.0625rem;
    color: var(--text-secondary);
    position: relative;
}

/* Pipeline status */
.pipeline-container {
    display: flex;
    gap: 0.75rem;
    overflow-x: auto;
    padding: 1rem 0;
}

.pipeline-stage {
    flex: 1;
    min-width: 120px;
    background: var(--bg-card);
    border: var(--border-subtle);
    border-radius: var(--radius-lg);
    padding: 1.25rem;
    text-align: center;
    transition: all 0.2s ease;
}

.pipeline-stage:hover {
    transform: translateY(-2px);
    box-shadow: var(--shadow-card);
}

.pipeline-stage.active {
    border-color: var(--accent-primary);
    background: var(--bg-accent);
}

.pipeline-count {
    font-family: 'Plus Jakarta Sans', sans-serif;
    font-size: 1.75rem;
    font-weight: 700;
    color: var(--text-primary);
}

.pipeline-label {
    font-family: 'Nunito Sans', sans-serif;
    font-size: 0.6875rem;
    color: var(--text-muted);
    text-transform: uppercase;
    letter-spacing: 0.05em;
    font-weight: 600;
}

/* Section headers */
.section-header {
    display: flex;
    align-items: center;
    gap: 1rem;
    margin: 2rem 0 1.25rem 0;
}

.section-title {
    font-family: 'Plus Jakarta Sans', sans-serif;
    font-size: 1.25rem;
    font-weight: 700;
    color: var(--text-primary);
}

.section-line {
    flex: 1;
    height: 2px;
    background: linear-gradient(90deg, var(--accent-primary), transparent);
    border-radius: 1px;
}

/* Empty state */
.empty-state {
    text-align: center;
    padding: 3rem 2rem;
    background: var(--bg-card);
    border: 2px dashed #E2E8F0;
    border-radius: var(--radius-xl);
}

.empty-state-icon {
    font-size: 3.5rem;
    margin-bottom: 1rem;
}

.empty-state-title {
    font-family: 'Plus Jakarta Sans', sans-serif;
    font-size: 1.125rem;
    font-weight: 700;
    color: var(--text-primary);
    margin-bottom: 0.5rem;
}

.empty-state-text {
    font-family: 'Nunito Sans', sans-serif;
    color: var(--text-muted);
}

/* Feature cards */
.feature-card {
    background: var(--bg-card);
    border: var(--border-subtle);
    border-radius: var(--radius-lg);
    padding: 1.5rem;
    transition: all 0.2s ease;
}

.feature-card:hover {
    border-color: var(--accent-primary);
    transform: translateY(-2px);
    box-shadow: var(--shadow-card);
}

.feature-icon {
    width: 48px;
    height: 48px;
    background: var(--gradient-primary);
    border-radius: var(--radius-md);
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1.5rem;
    margin-bottom: 1rem;
}

.feature-title {
    font-family: 'Plus Jakarta Sans', sans-serif;
    font-size: 1rem;
    font-weight: 700;
    color: var(--text-primary);
    margin-bottom: 0.375rem;
}

.feature-text {
    font-family: 'Nunito Sans', sans-serif;
    font-size: 0.875rem;
    color: var(--text-muted);
}
</style>
"""


def inject_styles():
    """Inject all custom styles into the Streamlit app."""
    import streamlit as st
    st.markdown(THEME_CSS, unsafe_allow_html=True)
    st.markdown(CARD_STYLES, unsafe_allow_html=True)


def job_card(title: str, company: str, location: str, tags: list = None,
             salary: str = None, match_score: float = None, url: str = None,
             schedule_ok: bool = None) -> str:
    """Generate HTML for a styled job card."""
    tags_html = ""
    if tags:
        for tag in tags:
            # Check if it's a source tag
            tag_lower = tag.lower()
            if tag_lower in ("indeed", "linkedin", "glassdoor"):
                tags_html += f'<span class="job-tag source-{tag_lower}">{tag}</span>'
            else:
                tags_html += f'<span class="job-tag">{tag}</span>'

    if salary:
        tags_html += f'<span class="job-tag salary">{salary}</span>'

    if match_score is not None:
        tags_html += f'<span class="job-tag match">{match_score:.0f}% match</span>'

    if schedule_ok is True:
        tags_html += '<span class="job-tag schedule-ok">Schedule OK</span>'
    elif schedule_ok is False:
        tags_html += '<span class="job-tag schedule-conflict">Schedule conflict</span>'

    title_html = f'<a href="{url}" target="_blank">{title}</a>' if url else title

    return f"""
    <div class="job-card">
        <div class="job-card-title">{title_html}</div>
        <div class="job-card-company">{company} · {location}</div>
        <div class="job-card-meta">{tags_html}</div>
    </div>
    """


def stat_card(value: str, label: str, variant: str = "default") -> str:
    """Generate HTML for a stat card."""
    value_class = "stat-value coral" if variant == "coral" else "stat-value"
    card_class = "stat-card coral" if variant == "coral" else "stat-card"

    return f"""
    <div class="{card_class}">
        <div class="{value_class}">{value}</div>
        <div class="stat-label">{label}</div>
    </div>
    """


def hero_section(title: str, subtitle: str) -> str:
    """Generate HTML for a hero section."""
    return f"""
    <div class="hero-section">
        <div class="hero-title">{title}</div>
        <div class="hero-subtitle">{subtitle}</div>
    </div>
    """


def section_header(title: str) -> str:
    """Generate HTML for a section header."""
    return f"""
    <div class="section-header">
        <div class="section-title">{title}</div>
        <div class="section-line"></div>
    </div>
    """


def empty_state(icon: str, title: str, text: str) -> str:
    """Generate HTML for an empty state."""
    return f"""
    <div class="empty-state">
        <div class="empty-state-icon">{icon}</div>
        <div class="empty-state-title">{title}</div>
        <div class="empty-state-text">{text}</div>
    </div>
    """


def feature_card(icon: str, title: str, text: str) -> str:
    """Generate HTML for a feature card."""
    return f"""
    <div class="feature-card">
        <div class="feature-icon">{icon}</div>
        <div class="feature-title">{title}</div>
        <div class="feature-text">{text}</div>
    </div>
    """


def pipeline_stage(count: int, label: str, active: bool = False) -> str:
    """Generate HTML for a pipeline stage."""
    active_class = " active" if active else ""
    return f"""
    <div class="pipeline-stage{active_class}">
        <div class="pipeline-count">{count}</div>
        <div class="pipeline-label">{label}</div>
    </div>
    """


def top_navigation(current_page: str = "") -> str:
    """Generate HTML for top navigation bar."""
    pages = [
        ("🏠 Home", "app", "/"),
        ("🔍 Search", "search", "/search"),
        ("📋 Tracker", "tracker", "/tracker"),
        ("📄 Resume", "resume", "/resume"),
        ("👤 Profile", "profile", "/profile"),
        ("⚙️ Settings", "settings", "/settings"),
    ]

    links_html = ""
    for label, page_id, url in pages:
        active_class = " active" if page_id == current_page else ""
        links_html += f'<span class="top-nav-link{active_class}" style="cursor: pointer;" data-page="{page_id}">{label}</span>'

    return f"""
    <div class="top-nav">
        <div class="top-nav-brand">⚔️ SideQuest</div>
        <div class="top-nav-links">
            {links_html}
        </div>
    </div>
    """


def skeleton_job_card(count: int = 1) -> str:
    """Generate HTML for skeleton job card loaders."""
    cards_html = ""
    for i in range(count):
        delay = i * 0.1
        cards_html += f"""
        <div class="skeleton-job-card" style="animation-delay: {delay}s;">
            <div class="skeleton skeleton-title"></div>
            <div class="skeleton skeleton-company"></div>
            <div class="skeleton-tags">
                <div class="skeleton skeleton-tag"></div>
                <div class="skeleton skeleton-tag"></div>
                <div class="skeleton skeleton-tag"></div>
            </div>
        </div>
        """
    return cards_html


def skeleton_stat_card(count: int = 1) -> str:
    """Generate HTML for skeleton stat card loaders."""
    cards_html = ""
    for i in range(count):
        delay = i * 0.1
        cards_html += f"""
        <div class="skeleton-stat-card" style="animation-delay: {delay}s;">
            <div class="skeleton skeleton-stat-value"></div>
            <div class="skeleton skeleton-stat-label"></div>
        </div>
        """
    return cards_html


def loading_spinner() -> str:
    """Generate HTML for a loading spinner overlay."""
    return """
    <div class="loading-overlay">
        <div class="loading-spinner"></div>
    </div>
    """


def loading_indicator(text: str = "Loading...") -> str:
    """Generate HTML for an inline loading indicator."""
    return f"""
    <div style="display: flex; align-items: center; gap: 0.75rem; padding: 1rem;">
        <div class="loading-spinner" style="width: 24px; height: 24px; border-width: 3px;"></div>
        <span style="font-family: 'Nunito Sans', sans-serif; color: var(--text-secondary);">{text}</span>
    </div>
    """


def danger_button_styles() -> str:
    """Return CSS to apply danger styling to Streamlit buttons using :has selector."""
    return """
    <style>
    /* Danger button styling for buttons with specific labels */
    .stButton:has(button:contains("Delete")),
    .stButton:has(button:contains("Remove")),
    .stButton:has(button:contains("Clear")) {
        button {
            background: #DC2626 !important;
            background-color: #DC2626 !important;
        }
        button:hover {
            background: #B91C1C !important;
            background-color: #B91C1C !important;
        }
    }
    </style>
    """
