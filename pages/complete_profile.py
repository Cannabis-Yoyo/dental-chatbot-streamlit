"""
Complete User Profile Page
"""
import streamlit as st
from datetime import date
from utils.db import get_session, User, UserProfile, UserClinicalInfo, get_karachi_time

# Styling
st.markdown("""
<style>
#MainMenu, header, footer {visibility:hidden;}
.stApp {background:#0f1419;font-family:"Inter",sans-serif;}

[data-testid="stSidebar"] {display: none;}

section.main > div.block-container {
  padding:0!important;margin:0!important;
  display:flex!important;
  align-items:center!important;
  justify-content:center!important;
  min-height:100vh!important;
}

.logo-section{text-align:center;border-bottom:1px solid #2a2a2a;
  margin-bottom:24px;padding-bottom:20px;}
.logo-text{color:#fff;font-size:18px;font-weight:600;margin-top:8px;}

.profile-card{background:#1a1a1a;border:1px solid #2a2a2a;border-radius:16px;
  width:500px;padding:32px 40px;box-shadow:0 0 18px rgba(0,0,0,.4);max-height:85vh;overflow-y:auto;}
.profile-title{color:#fff;font-size:20px;font-weight:600;text-align:center;margin-bottom:10px;}
.profile-subtitle{color:#9CA3AF;font-size:13px;text-align:center;margin-bottom:24px;}
.section-title{color:#5B9FED;font-size:16px;font-weight:600;margin:20px 0 12px 0;
  border-bottom:1px solid #2a2a2a;padding-bottom:8px;}

.stTextInput>div>div>input, .stTextArea>div>div>textarea, .stSelectbox>div>div>div,
.stDateInput>div>div>input{background:#111418;color:#fff;border:1px solid #2a2a2a;border-radius:8px;}

.progress-container{background:#2a2a2a;border-radius:8px;height:8px;margin-bottom:24px;}
.progress-bar{background:#5B9FED;height:100%;border-radius:8px;transition:width 0.3s;}

.warning-banner{background:#FEF3C7;border:1px solid #F59E0B;border-radius:8px;
  padding:12px 16px;margin-bottom:20px;color:#92400E;font-size:13px;text-align:center;}
</style>
""", unsafe_allow_html=True)

def show():
    """Main function to display profile completion"""
    
    if 'profile_step' not in st.session_state:
        st.session_state.profile_step = 1
    
    # Logo
    st.markdown("""
    <div class="logo-section">
        <div style="font-size:32px;">🦷</div>
        <div class="logo-text">Dental Care</div>
    </div>
    """, unsafe_allow_html=True)
    
    if st.session_state.profile_step == 1:
        show_personal_info_form()
    else:
        show_clinical_info_form()

def show_personal_info_form():
    """Step 1: Personal Information"""
    st.markdown('<div class="profile-card">', unsafe_allow_html=True)
    st.markdown('<div class="profile-title">Complete Your Profile</div>', unsafe_allow_html=True)
    st.markdown('<div class="profile-subtitle">Step 1 of 2: Personal Information</div>', unsafe_allow_html=True)
    
    st.markdown('<div class="warning-banner">Profile completion is mandatory to access the chat</div>', unsafe_allow_html=True)
    
    progress = 50
    st.markdown(f"""
    <div class="progress-container">
        <div class="progress-bar" style="width:{progress}%"></div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown('<div class="section-title">Personal Details</div>', unsafe_allow_html=True)
    
    with st.form("personal_info"):
        phone = st.text_input("Phone Number *", placeholder="e.g., +92 300 1234567")
        dob = st.date_input("Date of Birth *", min_value=date(1920, 1, 1), max_value=date.today(), value=None)
        gender = st.selectbox("Gender *", ["Select", "Male", "Female", "Other"])
        address = st.text_area("Address *", placeholder="Enter your complete address", height=100)
        
        st.markdown('<small style="color:#9CA3AF;">* Required fields</small>', unsafe_allow_html=True)
        
        submitted = st.form_submit_button("Next →", use_container_width=True)
        
        if submitted:
            if not phone or not phone.strip():
                st.error("Phone number is required")
            elif gender == "Select":
                st.error("Please select your gender")
            elif not address or not address.strip():
                st.error("Address is required")
            elif not dob:
                st.error("Date of birth is required")
            else:
                st.session_state.personal_info = {
                    "phone_number": phone.strip(),
                    "date_of_birth": dob,
                    "gender": gender,
                    "address": address.strip()
                }
                st.session_state.profile_step = 2
                st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)

def show_clinical_info_form():
    """Step 2: Clinical Information"""
    st.markdown('<div class="profile-card">', unsafe_allow_html=True)
    st.markdown('<div class="profile-title">Complete Your Profile</div>', unsafe_allow_html=True)
    st.markdown('<div class="profile-subtitle">Step 2 of 2: Clinical Information</div>', unsafe_allow_html=True)
    
    st.markdown('<div class="warning-banner">Please provide accurate medical information for better care</div>', unsafe_allow_html=True)
    
    progress = 100
    st.markdown(f"""
    <div class="progress-container">
        <div class="progress-bar" style="width:{progress}%"></div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown('<div class="section-title">Medical & Dental History</div>', unsafe_allow_html=True)
    
    with st.form("clinical_info"):
        allergies = st.text_area("Allergies", placeholder="List any allergies (medications, latex, etc.) or type 'None'", height=80)
        medications = st.text_area("Current Medications", placeholder="List any medications you're currently taking or type 'None'", height=80)
        past_procedures = st.text_area("Past Dental Procedures", placeholder="e.g., Root canal, Extraction, Braces or type 'None'", height=80)
        current_issues = st.text_area("Current Dental Issues", placeholder="Describe any current dental problems or type 'None'", height=80)
        last_visit = st.date_input("Last Dental Visit (Optional)", min_value=date(2000, 1, 1), max_value=date.today(), value=None)
        
        st.markdown('<small style="color:#9CA3AF;">All fields are required. Enter "None" if not applicable.</small>', unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        
        with col1:
            back_btn = st.form_submit_button("← Back", use_container_width=True)
        with col2:
            submit_btn = st.form_submit_button("Complete Profile", use_container_width=True)
        
        if back_btn:
            st.session_state.profile_step = 1
            st.rerun()
        
        if submit_btn:
            if not allergies or not allergies.strip():
                st.error("Please specify allergies or enter 'None'")
            elif not medications or not medications.strip():
                st.error("Please specify current medications or enter 'None'")
            elif not past_procedures or not past_procedures.strip():
                st.error("Please specify past dental procedures or enter 'None'")
            elif not current_issues or not current_issues.strip():
                st.error("Please specify current dental issues or enter 'None'")
            else:
                with st.spinner("Saving your profile..."):
                    result = save_complete_profile(
                        st.session_state.user_id,
                        st.session_state.personal_info,
                        {
                            "allergies": allergies.strip(),
                            "current_medications": medications.strip(),
                            "past_dental_procedures": past_procedures.strip(),
                            "current_dental_issues": current_issues.strip(),
                            "last_dental_visit": last_visit
                        }
                    )
                
                if result['success']:
                    st.success("Profile completed successfully!")
                    st.balloons()
                    import time
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error(result.get('error', 'Failed to save profile'))
    
    st.markdown('</div>', unsafe_allow_html=True)

def save_complete_profile(user_id: int, personal_info: dict, clinical_info: dict) -> dict:
    """Save complete user profile"""
    session = get_session()
    try:
        # Update or create profile
        profile = session.query(UserProfile).filter(UserProfile.user_id == user_id).first()
        if profile:
            profile.phone_number = personal_info['phone_number']
            profile.date_of_birth = personal_info['date_of_birth']
            profile.gender = personal_info['gender']
            profile.address = personal_info['address']
        else:
            profile = UserProfile(
                user_id=user_id,
                phone_number=personal_info['phone_number'],
                date_of_birth=personal_info['date_of_birth'],
                gender=personal_info['gender'],
                address=personal_info['address']
            )
            session.add(profile)
        
        # Update or create clinical info
        clinical = session.query(UserClinicalInfo).filter(UserClinicalInfo.user_id == user_id).first()
        if clinical:
            clinical.allergies = clinical_info['allergies']
            clinical.current_medications = clinical_info['current_medications']
            clinical.past_dental_procedures = clinical_info['past_dental_procedures']
            clinical.current_dental_issues = clinical_info['current_dental_issues']
            clinical.last_dental_visit = clinical_info['last_dental_visit']
        else:
            clinical = UserClinicalInfo(
                user_id=user_id,
                allergies=clinical_info['allergies'],
                current_medications=clinical_info['current_medications'],
                past_dental_procedures=clinical_info['past_dental_procedures'],
                current_dental_issues=clinical_info['current_dental_issues'],
                last_dental_visit=clinical_info['last_dental_visit']
            )
            session.add(clinical)
        
        session.commit()
        return {"success": True, "message": "Profile saved successfully"}
        
    except Exception as e:
        session.rollback()
        return {"success": False, "error": str(e)}
    finally:
        session.close()