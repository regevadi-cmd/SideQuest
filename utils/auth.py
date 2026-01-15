"""Authentication utilities for SideQuest with security hardening."""
import re
import time
import streamlit as st
from data.db_factory import Database
from config import DB_PATH
from utils.sanitize import safe_html

# Security constants
SESSION_TIMEOUT = 30 * 60  # 30 minutes in seconds
MAX_LOGIN_ATTEMPTS = 5
LOCKOUT_DURATION = 15 * 60  # 15 minutes in seconds
MIN_PASSWORD_LENGTH = 12


def init_auth():
    """Initialize authentication state."""
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    if "user" not in st.session_state:
        st.session_state.user = None
    if "db" not in st.session_state:
        st.session_state.db = Database(DB_PATH)
    if "session_start" not in st.session_state:
        st.session_state.session_start = time.time()
    if "last_activity" not in st.session_state:
        st.session_state.last_activity = time.time()


def check_session_timeout() -> bool:
    """Check if session has timed out due to inactivity.

    Returns:
        True if session is still valid, False if timed out
    """
    if not st.session_state.get("authenticated"):
        return True

    last_activity = st.session_state.get("last_activity", time.time())
    if time.time() - last_activity > SESSION_TIMEOUT:
        logout_user()
        return False

    # Update last activity
    st.session_state.last_activity = time.time()
    return True


def validate_password(password: str) -> tuple[bool, str]:
    """Validate password meets security requirements.

    Args:
        password: Password to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    if len(password) < MIN_PASSWORD_LENGTH:
        return False, f"Password must be at least {MIN_PASSWORD_LENGTH} characters"
    if not re.search(r'[A-Z]', password):
        return False, "Password must contain at least one uppercase letter"
    if not re.search(r'[a-z]', password):
        return False, "Password must contain at least one lowercase letter"
    if not re.search(r'[0-9]', password):
        return False, "Password must contain at least one number"
    if not re.search(r'[!@#$%^&*()_+\-=\[\]{};\':"\\|,.<>\/?]', password):
        return False, "Password must contain at least one special character"
    return True, ""


def check_login_lockout(username: str) -> tuple[bool, str]:
    """Check if user is locked out due to failed login attempts.

    Args:
        username: Username to check

    Returns:
        Tuple of (is_locked, message)
    """
    key = f"login_attempts_{username}"
    lockout_key = f"lockout_until_{username}"

    # Check if currently locked out
    lockout_until = st.session_state.get(lockout_key, 0)
    if time.time() < lockout_until:
        remaining = int(lockout_until - time.time()) // 60
        return True, f"Account temporarily locked. Try again in {remaining} minutes."

    return False, ""


def record_failed_login(username: str):
    """Record a failed login attempt.

    Args:
        username: Username that failed login
    """
    key = f"login_attempts_{username}"
    lockout_key = f"lockout_until_{username}"

    attempts = st.session_state.get(key, 0) + 1
    st.session_state[key] = attempts

    if attempts >= MAX_LOGIN_ATTEMPTS:
        st.session_state[lockout_key] = time.time() + LOCKOUT_DURATION
        st.session_state[key] = 0  # Reset counter


def clear_login_attempts(username: str):
    """Clear failed login attempts after successful login.

    Args:
        username: Username to clear
    """
    key = f"login_attempts_{username}"
    st.session_state[key] = 0


def login_user(username: str, password: str) -> tuple[bool, str]:
    """Attempt to log in a user with security checks.

    Args:
        username: Username
        password: Password

    Returns:
        Tuple of (success, message)
    """
    # Check lockout
    is_locked, message = check_login_lockout(username)
    if is_locked:
        return False, message

    db = st.session_state.db
    user = db.authenticate_user(username, password)

    if user:
        clear_login_attempts(username)
        st.session_state.authenticated = True
        st.session_state.user = user
        st.session_state.session_start = time.time()
        st.session_state.last_activity = time.time()
        return True, "Login successful!"

    record_failed_login(username)
    remaining_attempts = MAX_LOGIN_ATTEMPTS - st.session_state.get(f"login_attempts_{username}", 0)
    if remaining_attempts > 0:
        return False, f"Invalid username or password. {remaining_attempts} attempts remaining."
    return False, "Invalid username or password."


def signup_user(username: str, password: str, email: str = None) -> tuple[bool, str]:
    """Create a new user account with password validation.

    Args:
        username: Desired username
        password: Password
        email: Optional email address

    Returns:
        Tuple of (success, message)
    """
    if len(username) < 3:
        return False, "Username must be at least 3 characters"
    if len(username) > 50:
        return False, "Username must be less than 50 characters"
    if not re.match(r'^[a-zA-Z0-9_]+$', username):
        return False, "Username can only contain letters, numbers, and underscores"

    # Validate password strength
    is_valid, error = validate_password(password)
    if not is_valid:
        return False, error

    db = st.session_state.db
    user = db.create_user(username, password, email)
    if user:
        st.session_state.authenticated = True
        st.session_state.user = user
        st.session_state.session_start = time.time()
        st.session_state.last_activity = time.time()
        return True, "Account created successfully!"
    return False, "Username already exists"


def logout_user():
    """Log out the current user and clear session."""
    st.session_state.authenticated = False
    st.session_state.user = None
    st.session_state.session_start = None
    st.session_state.last_activity = None


def is_authenticated() -> bool:
    """Check if user is authenticated and session is valid."""
    if not st.session_state.get("authenticated", False):
        return False
    # Check session timeout
    return check_session_timeout()


def get_current_user():
    """Get the current logged-in user."""
    return st.session_state.get("user", None)


def require_auth():
    """Show login form if not authenticated. Returns True if authenticated."""
    init_auth()

    if is_authenticated():
        return True

    # Check if session timed out
    if st.session_state.get("session_timed_out"):
        st.warning("Your session has expired. Please log in again.")
        st.session_state.session_timed_out = False

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
            SideQuest
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
                    success, message = login_user(username, password)
                    if success:
                        st.success(message)
                        st.rerun()
                    else:
                        st.error(message)
                else:
                    st.error("Please enter both username and password")

    with tab_signup:
        st.markdown("""
        <div style="font-family: 'Plus Jakarta Sans', sans-serif; font-size: 1.25rem;
                    font-weight: 700; color: #0F172A; margin-bottom: 1rem;">
            Create your account
        </div>
        """, unsafe_allow_html=True)

        # Password requirements info
        st.markdown(f"""
        <div style="background: rgba(8, 145, 178, 0.08); border: 1px solid rgba(8, 145, 178, 0.2);
                    border-radius: 8px; padding: 0.75rem; margin-bottom: 1rem; font-size: 0.8rem; color: #475569;">
            <strong>Password requirements:</strong><br>
            - At least {MIN_PASSWORD_LENGTH} characters<br>
            - Uppercase and lowercase letters<br>
            - At least one number<br>
            - At least one special character
        </div>
        """, unsafe_allow_html=True)

        with st.form("signup_form"):
            new_username = st.text_input("Username", placeholder="Choose a username", key="signup_username")
            new_email = st.text_input("Email (optional)", placeholder="your@email.com", key="signup_email")
            new_password = st.text_input("Password", type="password", placeholder=f"Choose a password (min {MIN_PASSWORD_LENGTH} chars)", key="signup_password")
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
        # Sanitize username for XSS protection
        safe_username = safe_html(user.username) if user else "Unknown"

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
                    {safe_username}
                </div>
            </div>
            """, unsafe_allow_html=True)

            if st.button("Logout", key="logout_btn", use_container_width=True):
                logout_user()
                st.rerun()
