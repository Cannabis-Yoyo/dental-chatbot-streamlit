"""
Login and Signup page
"""
import streamlit as st
import time
from utils.auth import signup_user, verify_and_login, login_user

# Styling
st.markdown("""
<style>
#MainMenu, header, footer {visibility:hidden;}
.stApp {background:#0f1419;font-family:"Inter",sans-serif;}

section.main > div.block-container {
  padding:0!important;
  display:flex!important;
  align-items:center!important;
  justify-content:center!important;
  min-height:100vh!important;
}

.auth-card{background:#1a1a1a;border:1px solid #2a2a2a;border-radius:16px;
  width:450px;padding:24px 28px;box-shadow:0 0 18px rgba(0,0,0,.4);margin:0 auto;}

.auth-title{color:#fff;font-size:20px;font-weight:600;text-align:center;margin-bottom:24px;}

.stTextInput>div>div>input{background:#111418;color:#fff;border:1px solid #2a2a2a;border-radius:8px;}
.stTextInput>div>div>input:focus{border-color:#5B9FED;}

.logo-section{text-align:center;border-bottom:1px solid #2a2a2a;
  margin-bottom:24px;padding-bottom:20px;font-size:32px;}
.logo-text{color:#fff;font-size:18px;font-weight:600;margin-top:8px;}
</style>
""", unsafe_allow_html=True)

def show():
    """Main function to display login/signup"""
    
    # Initialize page state
    if 'current_page' not in st.session_state:
        st.session_state.current_page = 'login'
    
    # Logo
    st.markdown("""
    <div class="logo-section">
        <div style="font-size:32px;">🦷</div>
        <div class="logo-text">Dental Care</div>
    </div>
    """, unsafe_allow_html=True)
    
    # Check if awaiting verification
    if st.session_state.get('awaiting_verification', False):
        show_verification_form()
    elif st.session_state.current_page == 'signup':
        show_signup_form()
    else:
        show_login_form()

def show_login_form():
    """Display login form"""
    st.markdown('<div class="auth-card">', unsafe_allow_html=True)
    st.markdown('<div class="auth-title">User Login</div>', unsafe_allow_html=True)
    
    with st.form("login_form"):
        email = st.text_input("Email Address", placeholder="Enter your email")
        password = st.text_input("Password", placeholder="Enter your password", type="password")
        
        submitted = st.form_submit_button("Login", use_container_width=True)
        
        if submitted:
            if email and password:
                with st.spinner("Logging in..."):
                    result = login_user(email, password)
                
                if result['success']:
                    st.session_state.logged_in = True
                    st.session_state.user_id = result['user_id']
                    st.session_state.user_email = result['email']
                    st.success("Login successful! Redirecting...")
                    time.sleep(1)
                    st.rerun()
                else:
                    error_msg = result.get('error', 'Login failed')
                    if 'not verified' in error_msg.lower():
                        st.error("Please verify your email first")
                    elif 'invalid credentials' in error_msg.lower():
                        st.error("Invalid email or password")
                    else:
                        st.error(error_msg)
            else:
                st.warning("Please fill in all fields")
    
    if st.button("Don't have an account? Sign up", use_container_width=True, type="secondary"):
        st.session_state.current_page = 'signup'
        st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)

def show_signup_form():
    """Display signup form"""
    st.markdown('<div class="auth-card">', unsafe_allow_html=True)
    st.markdown('<div class="auth-title">Create Account</div>', unsafe_allow_html=True)
    
    with st.form("signup_form"):
        email = st.text_input("Email Address", placeholder="Enter your email")
        password = st.text_input("Password", placeholder="Create a password (min 8 characters)", type="password")
        confirm_password = st.text_input("Confirm Password", placeholder="Re-enter password", type="password")
        
        submitted = st.form_submit_button("Sign Up", use_container_width=True)
        
        if submitted:
            if not email or not password or not confirm_password:
                st.warning("Please fill all fields.")
            elif password != confirm_password:
                st.error("Passwords do not match.")
            elif len(password) < 8:
                st.warning("Password must be at least 8 characters long.")
            else:
                with st.spinner("Creating account..."):
                    result = signup_user(email, password)
                
                if result['success']:
                    st.success("Account created! Check your email for verification code.")
                    st.session_state.awaiting_verification = True
                    st.session_state.verification_email = email
                    st.session_state.signup_password = password
                    time.sleep(1.5)
                    st.rerun()
                else:
                    error_msg = result.get('error', 'Signup failed')
                    if 'already registered' in error_msg.lower():
                        st.error("This email is already registered. Please login.")
                    else:
                        st.error(error_msg)
    
    if st.button("Already have an account? Login", use_container_width=True, type="secondary"):
        st.session_state.current_page = 'login'
        st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)

def show_verification_form():
    """Display email verification form"""
    st.markdown('<div class="auth-card">', unsafe_allow_html=True)
    st.markdown('<div class="auth-title">Verify Your Email</div>', unsafe_allow_html=True)
    st.info(f"A verification code has been sent to **{st.session_state.verification_email}**")
    
    with st.form("verify_form"):
        code = st.text_input("Verification Code", placeholder="Enter 6-digit code", max_chars=6)
        
        col1, col2 = st.columns(2)
        
        with col1:
            verify_btn = st.form_submit_button("Verify", use_container_width=True)
        with col2:
            back_btn = st.form_submit_button("Back to Login", use_container_width=True)
        
        if verify_btn:
            if code and len(code) == 6:
                with st.spinner("Verifying..."):
                    result = verify_and_login(
                        st.session_state.verification_email,
                        code,
                        st.session_state.signup_password
                    )
                
                if result['success']:
                    st.success("Email verified! Redirecting to complete your profile...")
                    st.session_state.logged_in = True
                    st.session_state.user_id = result['user_id']
                    st.session_state.user_email = st.session_state.verification_email
                    st.session_state.awaiting_verification = False
                    st.session_state.verification_email = None
                    st.session_state.signup_password = None
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error(result.get('error', 'Verification failed'))
            else:
                st.warning("Please enter a valid 6-digit code")
        
        if back_btn:
            st.session_state.awaiting_verification = False
            st.session_state.verification_email = None
            st.session_state.current_page = 'login'
            st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)