"""Settings loading utility for persisted app settings."""
import streamlit as st
from data.db_factory import Database
from utils.encryption import decrypt_value


def load_settings(db: Database) -> None:
    """Load saved settings from database into session state.

    Call this on app startup to restore persisted settings.
    Only loads if not already loaded to avoid overwriting user changes.
    """
    if st.session_state.get("settings_loaded"):
        return

    # Load AI settings
    ai_settings = db.get_settings_dict("ai")
    if ai_settings:
        if ai_settings.get("provider"):
            st.session_state.ai_provider = ai_settings.get("provider")
        st.session_state.ai_provider_name = ai_settings.get("provider_name", "Claude (Anthropic)")
        # Decrypt API key when loading
        encrypted_key = ai_settings.get("api_key", "")
        st.session_state.ai_api_key = decrypt_value(encrypted_key) if encrypted_key else ""
        st.session_state.ai_model = ai_settings.get("model", "")
        st.session_state.ollama_url = ai_settings.get("ollama_url", "http://localhost:11434")

    # Load university job board settings
    uni_settings = db.get_settings_dict("uni")
    if uni_settings:
        st.session_state.university_job_board = {
            "name": uni_settings.get("name", ""),
            "url": uni_settings.get("url", ""),
            "use_auth": uni_settings.get("use_auth", False),
            "auth_cookie": uni_settings.get("auth_cookie", "")
        }

    st.session_state.settings_loaded = True
