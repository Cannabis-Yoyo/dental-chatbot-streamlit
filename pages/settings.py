"""
User Settings Page - Profile & Password Management
"""
import streamlit as st
from datetime import datetime, date
from utils.db import get_session, User, UserProfile, UserClinicalInfo
from utils.auth import change_password

st.markdown("""
<style>
#MainMenu, footer, header {visibility: hidden;}
.stApp { background: #0f1419; font-family: "Inter", sans-serif; }

.page-title {
    color: #ffffff;
    font-size: 28px;
    font-weight: 700;
    margin-bottom: 8px;
}
.page-subtitle {
    color: #9CA3AF;
    font-size: 14px;
    margin-bottom: 32px;
}

.settings-section {
    background: #1a1a1a;
    border: 1px solid #2a2a2a;
    border-radius: 12px;
    padding: 24px;
    margin-bottom: 20px;
}
.section-title {
    color: #ffffff;
    font-size: 18px;
    font-weight: 600;
    margin-bottom: 16px;
}

.profile-info {
    background: #111418;
    border: 1px solid #2a2a2a;
    border-radius: 8px;
    padding: 16px;
    margin-bottom: 16px;
}
.info-row {
    display: flex;
    justify-content: space-between;
    padding: 8px 0;
    border-bottom: 1px solid #2a2a2a;
}
.info-row:last-child {
    border-bottom: none;
}
.info-label {
    color: #9CA3AF;
    font-size: 14px;
}
.info-value {
    color: #ffffff;
    font-size: 14px;
    font-weight: 500;
}

.stTextInput>div>div>input,
.stTextArea>div>div>textarea,
.stDateInput>div>div>input,
.stSelectbox>div>div>select {
    background: #111418 !important;
    color: #ffffff !important;
    border: 1px solid #2a2a2a !important;
    border-radius: 8px !important;
}

.stButton>button {
    background: #5B9FED !important;
    color: white !important;
    border: none !important;
    border-radius: 8px !important;
}
</style>
""", unsafe_allow_html=True)

def show():
    """Display settings page"""
    
    col1, col2, col3 = st.columns([6, 1, 1])
    with col1:
        st.markdown('<div class="page-title">⚙️ Settings</div>', unsafe_allow_html=True)
        st.markdown('<div class="page-subtitle">Manage your profile and account settings</div>', unsafe_allow_html=True)
    with col2:
        if st.button("🏠 Chat", use_container_width=True):
            if 'show_settings' in st.session_state:
                del st.session_state.show_settings
            st.rerun()
    with col3:
        if st.button("🚪 Logout", use_container_width=True):
            from utils.auth import logout
            logout()
            st.rerun()
    
    # Fetch profile data
    session = get_session()
    try:
        user = session.query(User).filter(User.id == st.session_state.user_id).first()
        profile = session.query(UserProfile).filter(UserProfile.user_id == st.session_state.user_id).first()
        clinical = session.query(UserClinicalInfo).filter(UserClinicalInfo.user_id == st.session_state.user_id).first()
        
        if not user:
            st.error("User not found")
            return
        
        # Display current profile
        st.markdown('<div class="settings-section"><div class="section-title">👤 Current Profile</div>', unsafe_allow_html=True)
        st.markdown(f"""
        <div class="profile-info">
            <div class="info-row"><span class="info-label">Email:</span><span class="info-value">{user.email}</span></div>
            <div class="info-row"><span class="info-label">Phone:</span><span class="info-value">{profile.phone_number if profile and profile.phone_number else 'Not set'}</span></div>
            <div class="info-row"><span class="info-label">Date of Birth:</span><span class="info-value">{str(profile.date_of_birth) if profile and profile.date_of_birth else 'Not set'}</span></div>
            <div class="info-row"><span class="info-label">Gender:</span><span class="info-value">{profile.gender if profile and profile.gender else 'Not set'}</span></div>
            <div class="info-row"><span class="info-label">Address:</span><span class="info-value">{profile.address if profile and profile.address else 'Not set'}</span></div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Update Personal Info
        st.markdown('<div class="settings-section"><div class="section-title">✏️ Update Personal Info</div>', unsafe_allow_html=True)
        with st.form("update_personal"):
            col1, col2 = st.columns(2)
            with col1:
                phone = st.text_input("Phone", value=profile.phone_number if profile and profile.phone_number else '')
                dob_value = None
                if profile and profile.date_of_birth:
                    try:
                        if isinstance(profile.date_of_birth, str):
                            dob_value = datetime.strptime(profile.date_of_birth, '%Y-%m-%d').date()
                        else:
                            dob_value = profile.date_of_birth
                    except:
                        pass
                dob = st.date_input("Date of Birth", value=dob_value)
            with col2:
                gender_options = ["Male", "Female", "Other"]
                current_gender = profile.gender if profile and profile.gender else 'Male'
                gender_index = gender_options.index(current_gender) if current_gender in gender_options else 0
                gender = st.selectbox("Gender", gender_options, index=gender_index)
                address = st.text_area("Address", value=profile.address if profile and profile.address else '', height=100)
            
            if st.form_submit_button("Update Personal Info", use_container_width=True):
                result = update_personal_info(
                    st.session_state.user_id,
                    phone if phone else None,
                    dob if dob else None,
                    gender,
                    address if address else None
                )
                if result['success']:
                    st.success("Personal info updated successfully!")
                    st.rerun()
                else:
                    st.error(f"Failed to update: {result.get('error')}")
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Update Clinical Info
        st.markdown('<div class="settings-section"><div class="section-title">🥼 Update Clinical Info</div>', unsafe_allow_html=True)
        with st.form("update_clinical"):
            allergies = st.text_area("Allergies", value=clinical.allergies if clinical and clinical.allergies else '', height=80)
            medications = st.text_area("Current Medications", value=clinical.current_medications if clinical and clinical.current_medications else '', height=80)
            procedures = st.text_area("Past Dental Procedures", value=clinical.past_dental_procedures if clinical and clinical.past_dental_procedures else '', height=80)
            issues = st.text_area("Current Dental Issues", value=clinical.current_dental_issues if clinical and clinical.current_dental_issues else '', height=80)
            
            last_visit_value = None
            if clinical and clinical.last_dental_visit:
                try:
                    if isinstance(clinical.last_dental_visit, str):
                        last_visit_value = datetime.strptime(clinical.last_dental_visit, '%Y-%m-%d').date()
                    else:
                        last_visit_value = clinical.last_dental_visit
                except:
                    pass
            last_visit = st.date_input("Last Dental Visit", value=last_visit_value)
            
            if st.form_submit_button("Update Clinical Info", use_container_width=True):
                result = update_clinical_info(
                    st.session_state.user_id,
                    allergies if allergies else None,
                    medications if medications else None,
                    procedures if procedures else None,
                    issues if issues else None,
                    last_visit if last_visit else None
                )
                if result['success']:
                    st.success("Clinical info updated successfully!")
                    st.rerun()
                else:
                    st.error(f"Failed to update: {result.get('error')}")
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Change Password
        st.markdown('<div class="settings-section"><div class="section-title">🔒 Change Password</div>', unsafe_allow_html=True)
        with st.form("change_password"):
            current_pwd = st.text_input("Current Password", type="password")
            new_pwd = st.text_input("New Password", type="password")
            confirm_pwd = st.text_input("Confirm New Password", type="password")
            
            if st.form_submit_button("Change Password", use_container_width=True):
                if not current_pwd or not new_pwd or not confirm_pwd:
                    st.warning("Fill all password fields")
                elif len(new_pwd) < 8:
                    st.warning("Password must be 8+ characters")
                elif new_pwd != confirm_pwd:
                    st.error("Passwords don't match")
                else:
                    result = change_password(st.session_state.user_id, current_pwd, new_pwd)
                    if result['success']:
                        st.success("Password changed successfully!")
                    else:
                        st.error(result.get('error'))
        st.markdown('</div>', unsafe_allow_html=True)
        
    finally:
        session.close()

def update_personal_info(user_id, phone, dob, gender, address):
    """Update personal information"""
    session = get_session()
    try:
        profile = session.query(UserProfile).filter(UserProfile.user_id == user_id).first()
        if profile:
            profile.phone_number = phone
            profile.date_of_birth = dob
            profile.gender = gender
            profile.address = address
        else:
            profile = UserProfile(
                user_id=user_id,
                phone_number=phone,
                date_of_birth=dob,
                gender=gender,
                address=address
            )
            session.add(profile)
        
        session.commit()
        return {"success": True}
    except Exception as e:
        session.rollback()
        return {"success": False, "error": str(e)}
    finally:
        session.close()

def update_clinical_info(user_id, allergies, medications, procedures, issues, last_visit):
    """Update clinical information"""
    session = get_session()
    try:
        clinical = session.query(UserClinicalInfo).filter(UserClinicalInfo.user_id == user_id).first()
        if clinical:
            clinical.allergies = allergies
            clinical.current_medications = medications
            clinical.past_dental_procedures = procedures
            clinical.current_dental_issues = issues
            clinical.last_dental_visit = last_visit
        else:
            clinical = UserClinicalInfo(
                user_id=user_id,
                allergies=allergies,
                current_medications=medications,
                past_dental_procedures=procedures,
                current_dental_issues=issues,
                last_dental_visit=last_visit
            )
            session.add(clinical)
        
        session.commit()
        return {"success": True}
    except Exception as e:
        session.rollback()
        return {"success": False, "error": str(e)}
    finally:
        session.close()