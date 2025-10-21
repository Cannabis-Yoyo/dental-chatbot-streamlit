"""
Dental Care Chatbot - Streamlit Application
Main entry point for the application
"""
import streamlit as st
from pathlib import Path
import sys
import traceback

# Add utils to path
sys.path.insert(0, str(Path(__file__).parent))

# Configure page FIRST before any other Streamlit commands
st.set_page_config(
    page_title="Dental Care",
    page_icon="🦷",
    layout="wide",
    initial_sidebar_state="auto"
)

try:
    from utils.auth import init_session_state
    from utils.db import init_database
    
    # Initialize database tables
    init_database()
    
    # Initialize session state
    init_session_state()
    
    # Check authentication and route
    if not st.session_state.get('logged_in', False):
        # Show login/signup page
        from pages import login_signup
        login_signup.show()
    elif st.session_state.get('show_settings', False):
        # Show settings page
        from pages import settings
        settings.show()
    else:
        # Check if profile is complete
        from utils.db import check_profile_complete
        
        if not check_profile_complete(st.session_state.user_id):
            # Show complete profile page
            from pages import complete_profile
            complete_profile.show()
        else:
            # Show main chat interface
            from pages import main_chat
            main_chat.show()

except Exception as e:
    st.error(f"Application Error: {str(e)}")
    st.code(traceback.format_exc())
    st.info("Please check your configuration and try again.")