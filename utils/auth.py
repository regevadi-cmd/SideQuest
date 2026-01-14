"""Authentication utilities for SideQuest."""
import streamlit as st
from data.db_factory import Database
from config import DB_PATH


def init_auth():
    """Initialize authentication state."""
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    if "user" not in st.session_state:
        st.session_state.user = None
    if "db" not in st.session_state:
        st.session_state.db = Database(DB_PATH)


def login_user(username: str, password: str) -> bool:
    """Attempt to log in a user."""
    db = st.session_state.db
    user = db.authenticate_user(username, password)
    if user:
        st.session_state.authenticated = True
        st.session_state.user = user
        return True
    return False


def signup_user(username: str, password: str, email: str = None) -> tuple[bool, str]:
    """Create a new user account."""
    if len(username) < 3:
        return False, "Username must be at least 3 characters"
    if len(password) < 6:
        return False, "Password must be at least 6 characters"

    db = st.session_state.db
    user = db.create_user(username, password, email)
    if user:
        st.session_state.authenticated = True
        st.session_state.user = user
        return True, "Account created successfully!"
    return False, "Username already exists"


def logout_user():
    """Log out the current user."""
    st.session_state.authenticated = False
    st.session_state.user = None


def is_authenticated() -> bool:
    """Check if user is authenticated."""
    return st.session_state.get("authenticated", False)


def get_current_user():
    """Get the current logged-in user."""
    return st.session_state.get("user", None)


def require_auth():
    """Show login form if not authenticated. Returns True if authenticated."""
    init_auth()

    if is_authenticated():
        return True

    show_login_page()
    return False


def show_login_page():
    """Display the login/signup page."""
    st.markdown("""
    <div style="text-align: center; padding: 2rem 0;">
        <div style="font-family: 'Plus Jakarta Sans', sans-serif; font-size: 2.5rem; font-weight: 800;
                    background: linear-gradient(135deg, #0891B2 0%, #22D3EE 100%);
                    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
                    margin-bottom: 0.5rem;">
            ⚔️ SideQuest
        </div>
        <div style="color: #94A3B8; font-size: 1rem;">
            Find your next adventure
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Check if any user exists
    db = st.session_state.db
    has_users = db.user_exists()

    if has_users:
        tab_login, tab_signup = st.tabs(["Login", "Create Account"])
    else:
        tab_signup, tab_login = st.tabs(["Create Account", "Login"])
        st.info("Welcome! Create an account to get started.")

    with tab_login:
        st.markdown("""
        <div style="font-family: 'Plus Jakarta Sans', sans-serif; font-size: 1.25rem;
                    font-weight: 700; color: #0F172A; margin-bottom: 1rem;">
            Welcome back
        </div>
        """, unsafe_allow_html=True)

        with st.form("login_form"):
            username = st.text_input("Username", placeholder="Enter your username")
            password = st.text_input("Password", type="password", placeholder="Enter your password")
            submit = st.form_submit_button("Login", type="primary", use_container_width=True)

            if submit:
                if username and password:
                    if login_user(username, password):
                        st.success("Login successful!")
                        st.rerun()
                    else:
                        st.error("Invalid username or password")
                else:
                    st.error("Please enter both username and password")

    with tab_signup:
        st.markdown("""
        <div style="font-family: 'Plus Jakarta Sans', sans-serif; font-size: 1.25rem;
                    font-weight: 700; color: #0F172A; margin-bottom: 1rem;">
            Create your account
        </div>
        """, unsafe_allow_html=True)

        with st.form("signup_form"):
            new_username = st.text_input("Username", placeholder="Choose a username", key="signup_username")
            new_email = st.text_input("Email (optional)", placeholder="your@email.com", key="signup_email")
            new_password = st.text_input("Password", type="password", placeholder="Choose a password (min 6 characters)", key="signup_password")
            confirm_password = st.text_input("Confirm Password", type="password", placeholder="Confirm your password", key="signup_confirm")
            submit = st.form_submit_button("Create Account", type="primary", use_container_width=True)

            if submit:
                if not new_username or not new_password:
                    st.error("Please enter username and password")
                elif new_password != confirm_password:
                    st.error("Passwords do not match")
                else:
                    success, message = signup_user(new_username, new_password, new_email if new_email else None)
                    if success:
                        st.success(message)
                        st.rerun()
                    else:
                        st.error(message)


def show_user_menu():
    """Show user menu in sidebar when authenticated."""
    if is_authenticated():
        user = get_current_user()
        with st.sidebar:
            st.markdown(f"""
            <div style="padding: 0.75rem; background: rgba(8, 145, 178, 0.08);
                        border: 1px solid rgba(8, 145, 178, 0.2); border-radius: 12px;
                        margin-bottom: 1rem;">
                <div style="font-family: 'Plus Jakarta Sans', sans-serif; font-size: 0.75rem;
                            color: #94A3B8; text-transform: uppercase; margin-bottom: 0.25rem;">
                    Logged in as
                </div>
                <div style="font-family: 'Plus Jakarta Sans', sans-serif; font-weight: 700;
                            color: #0891B2;">
                    {user.username}
                </div>
            </div>
            """, unsafe_allow_html=True)

            if st.button("Logout", key="logout_btn", use_container_width=True):
                logout_user()
                st.rerun()
