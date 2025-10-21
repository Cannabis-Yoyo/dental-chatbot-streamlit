"""
Authentication module
Handles user signup, login, verification
"""
import streamlit as st
import bcrypt
import jwt
from datetime import datetime, timedelta
from utils.db import get_session, User, get_karachi_time, KARACHI_TZ
from utils.helpers import generate_verification_code, send_verification_email

def init_session_state():
    """Initialize session state variables"""
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
    if 'user_id' not in st.session_state:
        st.session_state.user_id = None
    if 'user_email' not in st.session_state:
        st.session_state.user_email = None
    if 'awaiting_verification' not in st.session_state:
        st.session_state.awaiting_verification = False
    if 'verification_email' not in st.session_state:
        st.session_state.verification_email = None
    if 'signup_password' not in st.session_state:
        st.session_state.signup_password = None

def hash_password(password: str) -> str:
    """Hash password using bcrypt"""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against hash"""
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))

def create_access_token(email: str) -> str:
    """Create JWT access token"""
    expire = datetime.utcnow() + timedelta(minutes=int(st.secrets.get('ACCESS_TOKEN_EXPIRE_MINUTES', 1440)))
    payload = {"sub": email, "exp": expire}
    return jwt.encode(payload, st.secrets['SECRET_KEY'], algorithm=st.secrets.get('ALGORITHM', 'HS256'))

def signup_user(email: str, password: str) -> dict:
    """
    Register new user
    Returns: {"success": bool, "message": str, "error": str (optional)}
    """
    session = get_session()
    try:
        # Check if user exists
        existing = session.query(User).filter(User.email == email).first()
        if existing:
            return {"success": False, "error": "Email already registered"}
        
        # Generate verification code
        code = generate_verification_code()
        code_expires = get_karachi_time() + timedelta(minutes=10)
        
        # Create user
        new_user = User(
            email=email,
            password_hash=hash_password(password),
            verification_code=code,
            verification_code_expires_at=code_expires,
            created_at=get_karachi_time()
        )
        
        session.add(new_user)
        session.commit()
        
        # Send email
        email_sent = send_verification_email(email, code)
        
        if not email_sent:
            return {"success": True, "message": "User created but email failed to send", "code": code}
        
        return {"success": True, "message": "Verification code sent to email"}
        
    except Exception as e:
        session.rollback()
        return {"success": False, "error": str(e)}
    finally:
        session.close()

def verify_code(email: str, code: str) -> dict:
    """
    Verify email with code
    Returns: {"success": bool, "message": str, "error": str (optional)}
    """
    session = get_session()
    try:
        user = session.query(User).filter(User.email == email).first()
        
        if not user:
            return {"success": False, "error": "User not found"}
        
        if user.is_verified:
            return {"success": False, "error": "User already verified"}
        
        if user.verification_code != code:
            return {"success": False, "error": "Invalid verification code"}
        
        if get_karachi_time() > user.verification_code_expires_at.replace(tzinfo=KARACHI_TZ):
            return {"success": False, "error": "Verification code expired"}
        
        # Mark as verified
        user.is_verified = True
        user.verification_code = None
        user.verification_code_expires_at = None
        session.commit()
        
        return {"success": True, "message": "Email verified successfully"}
        
    except Exception as e:
        session.rollback()
        return {"success": False, "error": str(e)}
    finally:
        session.close()

def login_user(email: str, password: str) -> dict:
    """
    Login user
    Returns: {"success": bool, "user_id": int, "message": str, "error": str (optional)}
    """
    session = get_session()
    try:
        user = session.query(User).filter(User.email == email).first()
        
        if not user or not verify_password(password, user.password_hash):
            return {"success": False, "error": "Invalid credentials"}
        
        if not user.is_verified:
            return {"success": False, "error": "Email not verified"}
        
        return {
            "success": True,
            "user_id": user.id,
            "email": user.email,
            "message": "Login successful"
        }
        
    except Exception as e:
        return {"success": False, "error": str(e)}
    finally:
        session.close()

def verify_and_login(email: str, code: str, password: str) -> dict:
    """
    Verify email and automatically login
    Returns: {"success": bool, "user_id": int, "message": str, "error": str (optional)}
    """
    verify_result = verify_code(email, code)
    if not verify_result['success']:
        return verify_result
    
    return login_user(email, password)

def change_password(user_id: int, current_password: str, new_password: str) -> dict:
    """
    Change user password
    Returns: {"success": bool, "message": str, "error": str (optional)}
    """
    session = get_session()
    try:
        user = session.query(User).filter(User.id == user_id).first()
        
        if not user:
            return {"success": False, "error": "User not found"}
        
        if not verify_password(current_password, user.password_hash):
            return {"success": False, "error": "Current password is incorrect"}
        
        user.password_hash = hash_password(new_password)
        session.commit()
        
        return {"success": True, "message": "Password changed successfully"}
        
    except Exception as e:
        session.rollback()
        return {"success": False, "error": str(e)}
    finally:
        session.close()

def logout():
    """Clear session state and logout"""
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    init_session_state()