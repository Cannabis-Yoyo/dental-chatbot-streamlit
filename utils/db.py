"""
Database connection and operations module
Handles all database interactions using SQLAlchemy
"""
import streamlit as st
from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime, Text, ForeignKey, Date, Time
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import pytz

KARACHI_TZ = pytz.timezone('Asia/Karachi')

def get_karachi_time():
    return datetime.now(KARACHI_TZ)

Base = declarative_base()

# Define Models (same as original)
class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    full_name = Column(String, nullable=True)
    is_verified = Column(Boolean, default=False)
    verification_code = Column(String, nullable=True)
    verification_code_expires_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime(timezone=True), default=get_karachi_time)
    
    profile = relationship("UserProfile", back_populates="user", uselist=False)
    clinical_info = relationship("UserClinicalInfo", back_populates="user", uselist=False)
    chat_sessions = relationship("ChatSession", back_populates="user")
    appointments = relationship("Appointment", back_populates="user")

class UserProfile(Base):
    __tablename__ = "user_profiles"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True)
    phone_number = Column(String, nullable=True)
    date_of_birth = Column(Date, nullable=True)
    gender = Column(String, nullable=True)
    address = Column(Text, nullable=True)
    
    user = relationship("User", back_populates="profile")

class UserClinicalInfo(Base):
    __tablename__ = "user_clinical_info"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True)
    allergies = Column(Text, nullable=True)
    current_medications = Column(Text, nullable=True)
    past_dental_procedures = Column(Text, nullable=True)
    current_dental_issues = Column(Text, nullable=True)
    last_dental_visit = Column(Date, nullable=True)
    
    user = relationship("User", back_populates="clinical_info")

class ChatSession(Base):
    __tablename__ = "chat_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    title = Column(String, default="New Chat")
    created_at = Column(DateTime(timezone=True), default=get_karachi_time)
    updated_at = Column(DateTime(timezone=True), default=get_karachi_time, onupdate=get_karachi_time)
    
    user = relationship("User", back_populates="chat_sessions")
    messages = relationship("ChatMessage", back_populates="session", cascade="all, delete-orphan")

class ChatMessage(Base):
    __tablename__ = "chat_messages"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("chat_sessions.id"))
    role = Column(String, nullable=False)
    message = Column(Text, nullable=False)
    timestamp = Column(DateTime(timezone=True), default=get_karachi_time)
    
    session = relationship("ChatSession", back_populates="messages")

class Appointment(Base):
    __tablename__ = "appointments"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    branch = Column(String, nullable=False)
    dentist = Column(String, nullable=False)
    treatment_type = Column(String, nullable=False)
    appointment_date = Column(Date, nullable=False)
    appointment_time = Column(Time, nullable=False)
    status = Column(String, default="scheduled")
    created_at = Column(DateTime(timezone=True), default=get_karachi_time)
    
    user = relationship("User", back_populates="appointments")

# Database connection
@st.cache_resource
def get_engine():
    """Create database engine from Streamlit secrets"""
    db_url = f"postgresql://{st.secrets['DB_USER']}:{st.secrets['DB_PASS']}@{st.secrets['DB_HOST']}:{st.secrets['DB_PORT']}/{st.secrets['DB_NAME']}"
    return create_engine(db_url, pool_pre_ping=True)

def get_session():
    """Get database session"""
    engine = get_engine()
    Session = sessionmaker(bind=engine)
    return Session()

def init_database():
    """Initialize database tables"""
    engine = get_engine()
    Base.metadata.create_all(engine)

def check_profile_complete(user_id: int) -> bool:
    """Check if user profile is complete"""
    session = get_session()
    try:
        profile = session.query(UserProfile).filter(UserProfile.user_id == user_id).first()
        clinical = session.query(UserClinicalInfo).filter(UserClinicalInfo.user_id == user_id).first()
        return profile is not None and clinical is not None
    finally:
        session.close()

def get_user_profile_dict(user_id: int) -> dict:
    """Get complete user profile as dictionary"""
    session = get_session()
    try:
        user = session.query(User).filter(User.id == user_id).first()
        if not user:
            return {}
        
        profile = session.query(UserProfile).filter(UserProfile.user_id == user_id).first()
        clinical = session.query(UserClinicalInfo).filter(UserClinicalInfo.user_id == user_id).first()
        
        profile_data = {}
        if profile:
            profile_data = {
                "phone_number": profile.phone_number,
                "date_of_birth": str(profile.date_of_birth) if profile.date_of_birth else None,
                "gender": profile.gender,
                "address": profile.address
            }
        
        clinical_data = {}
        if clinical:
            clinical_data = {
                "allergies": clinical.allergies,
                "current_medications": clinical.current_medications,
                "past_dental_procedures": clinical.past_dental_procedures,
                "current_dental_issues": clinical.current_dental_issues,
                "last_dental_visit": str(clinical.last_dental_visit) if clinical.last_dental_visit else None
            }
        
        return {
            "id": user.id,
            "email": user.email,
            "full_name": user.full_name,
            "profile": profile_data,
            "clinical_info": clinical_data
        }
    finally:
        session.close()