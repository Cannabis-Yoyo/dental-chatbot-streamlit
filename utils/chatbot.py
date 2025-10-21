"""
RAG Chatbot Integration Module - FIXED BOOKING LOOP
Handles chat message processing, appointment booking, and name extraction
"""
import streamlit as st
import re
from datetime import datetime, date, time, timedelta
from typing import List, Dict, Optional, Tuple
import traceback

from utils.db import (
    get_session, ChatSession, ChatMessage, User, Appointment,
    get_karachi_time, get_user_profile_dict
)
from utils.helpers import send_appointment_confirmation
from rag.rag_chatbot import RAGChatbot

@st.cache_resource
def get_rag_chatbot():
    """Initialize and cache RAG chatbot"""
    import os
    from pathlib import Path
    
    BASE_DIR = Path(__file__).parent.parent
    knowledge_base_path = BASE_DIR / "rag" / "data.json"
    groq_api_key = st.secrets['GROQ_API_KEY']
    
    return RAGChatbot(str(knowledge_base_path), groq_api_key)

def extract_name_from_message(message: str) -> Optional[str]:
    """Extract name from user message"""
    msg_lower = message.lower().strip()
    
    if len(msg_lower) < 2:
        return None
    
    ignore_words = ['hi', 'hello', 'hey', 'yes', 'no', 'okay', 'ok', 'sure', 'thanks', 'thank',
                    'please', 'good', 'fine', 'great', 'nice', 'morning', 'evening', 'afternoon',
                    'book', 'appointment', 'help', 'need', 'want', 'can', 'could', 'would', 'my']
    
    patterns = [
        r"(?:my name is|i'?m|i am|call me|this is|it'?s)\s+([a-z][a-z\s]{1,30})",
        r"^([a-z][a-z]{1,20})$"
    ]
    
    for pattern in patterns:
        match = re.search(pattern, msg_lower)
        if match:
            name = match.group(1).strip()
            name_parts = name.split()
            if len(name_parts) > 0:
                clean_name = ' '.join(name_parts[:2])
                if clean_name.lower() not in ignore_words and len(clean_name) >= 2:
                    return ' '.join(word.capitalize() for word in clean_name.split())
    
    return None

def parse_natural_date(text: str) -> Optional[str]:
    """Parse natural language date - FIXED VERSION"""
    text_lower = text.lower().strip()
    today = datetime.now().date()
    current_year = today.year
    
    # Handle relative dates
    if 'today' in text_lower:
        return today.strftime('%Y-%m-%d')
    if 'tomorrow' in text_lower:
        return (today + timedelta(days=1)).strftime('%Y-%m-%d')
    if 'day after tomorrow' in text_lower:
        return (today + timedelta(days=2)).strftime('%Y-%m-%d')
    
    # Month names mapping
    months = {
        'jan': 1, 'january': 1, 'feb': 2, 'february': 2, 'mar': 3, 'march': 3,
        'apr': 4, 'april': 4, 'may': 5, 'jun': 6, 'june': 6,
        'jul': 7, 'july': 7, 'aug': 8, 'august': 8, 'sep': 9, 'sept': 9, 'september': 9,
        'oct': 10, 'october': 10, 'nov': 11, 'november': 11, 'dec': 12, 'december': 12
    }
    
    # Parse month and day combinations
    for month_name, month_num in months.items():
        # Pattern: "27 october" or "27th october"
        pattern1 = rf'\b(\d{{1,2}})(?:st|nd|rd|th)?\s+{month_name}\b'
        match1 = re.search(pattern1, text_lower)
        if match1:
            day = int(match1.group(1))
            try:
                parsed_date = datetime(current_year, month_num, day).date()
                # If date is in the past, assume next year
                if parsed_date < today:
                    parsed_date = datetime(current_year + 1, month_num, day).date()
                return parsed_date.strftime('%Y-%m-%d')
            except ValueError:
                continue
        
        # Pattern: "october 27" or "october 27th"
        pattern2 = rf'\b{month_name}\s+(\d{{1,2}})(?:st|nd|rd|th)?\b'
        match2 = re.search(pattern2, text_lower)
        if match2:
            day = int(match2.group(1))
            try:
                parsed_date = datetime(current_year, month_num, day).date()
                # If date is in the past, assume next year
                if parsed_date < today:
                    parsed_date = datetime(current_year + 1, month_num, day).date()
                return parsed_date.strftime('%Y-%m-%d')
            except ValueError:
                continue
    
    # Weekday parsing
    weekdays = {
        'monday': 0, 'tuesday': 1, 'wednesday': 2, 'thursday': 3,
        'friday': 4, 'saturday': 5, 'sunday': 6,
        'mon': 0, 'tue': 1, 'wed': 2, 'thu': 3, 'fri': 4, 'sat': 5, 'sun': 6
    }
    
    for day_name, day_num in weekdays.items():
        if f'next {day_name}' in text_lower or f'this {day_name}' in text_lower:
            days_ahead = day_num - today.weekday()
            if days_ahead <= 0:
                days_ahead += 7
            target_date = today + timedelta(days=days_ahead)
            return target_date.strftime('%Y-%m-%d')
    
    # Standard date formats
    pattern_standard = r'\b(\d{4})-(\d{2})-(\d{2})\b'
    match_standard = re.search(pattern_standard, text)
    if match_standard:
        return match_standard.group(0)
    
    pattern_slash = r'\b(\d{1,2})[/-](\d{1,2})[/-](\d{4})\b'
    match_slash = re.search(pattern_slash, text)
    if match_slash:
        day, month, year = match_slash.groups()
        try:
            parsed_date = datetime(int(year), int(month), int(day)).date()
            return parsed_date.strftime('%Y-%m-%d')
        except ValueError:
            pass
    
    return None

def parse_natural_time(text: str) -> Optional[str]:
    """Parse natural language time"""
    text_lower = text.lower().strip()
    
    pattern_ampm = r'\b(\d{1,2})\s*(am|pm)\b'
    match_ampm = re.search(pattern_ampm, text_lower)
    if match_ampm:
        hour = int(match_ampm.group(1))
        period = match_ampm.group(2)
        if period == 'pm' and hour != 12:
            hour += 12
        elif period == 'am' and hour == 12:
            hour = 0
        return f"{hour:02d}:00"
    
    pattern_time_ampm = r'\b(\d{1,2}):(\d{2})\s*(am|pm)\b'
    match_time_ampm = re.search(pattern_time_ampm, text_lower)
    if match_time_ampm:
        hour = int(match_time_ampm.group(1))
        minute = int(match_time_ampm.group(2))
        period = match_time_ampm.group(3)
        if period == 'pm' and hour != 12:
            hour += 12
        elif period == 'am' and hour == 12:
            hour = 0
        return f"{hour:02d}:{minute:02d}"
    
    pattern_24h = r'\b(\d{1,2}):(\d{2})\b'
    match_24h = re.search(pattern_24h, text)
    if match_24h:
        hour = int(match_24h.group(1))
        minute = int(match_24h.group(2))
        if 0 <= hour <= 23 and 0 <= minute <= 59:
            return f"{hour:02d}:{minute:02d}"
    
    return None

def parse_booking_data(message: str, chat_history: List) -> dict:
    """Extract booking information from message and chat history"""
    booking_data = {}
    
    all_messages = []
    for msg in chat_history[-15:]:
        all_messages.append(msg.message)
    all_messages.append(message)
    
    full_context = ' '.join(all_messages)
    full_context_lower = full_context.lower()
    
    date_str, time_str = extract_datetime_from_conversation(message, chat_history)
    
    if date_str:
        booking_data['date'] = date_str
    
    if time_str:
        booking_data['time'] = time_str
    
    if 'dha' in full_context_lower:
        booking_data['branch'] = 'NeoImplant - DHA'
    elif 'clifton' in full_context_lower:
        booking_data['branch'] = 'NeoImplant - Clifton'
    
    if 'fatima' in full_context_lower:
        booking_data['dentist'] = 'Dr. Fatima Khan'
    elif 'ahmed' in full_context_lower or 'raza' in full_context_lower:
        booking_data['dentist'] = 'Dr. Ahmed Raza'
    
    treatment_keywords = {
        'crown': 'Dental Crown',
        'crowning': 'Dental Crown',
        'scaling': 'Scaling and Polishing',
        'cleaning': 'Scaling and Polishing',
        'filling': 'Dental Filling',
        'implant': 'Dental Implant',
        'root canal': 'Root Canal Treatment',
        'extraction': 'Tooth Extraction',
        'consultation': 'Consultation',
        'checkup': 'General Checkup',
        'check-up': 'General Checkup',
        'discussion': 'Discussion and Diagnosis',
        'diagnosis': 'Discussion and Diagnosis',
        'exam': 'Dental Examination',
        'bleeding gums': 'Gum Treatment',
        'gum': 'Gum Treatment'
    }
    
    for keyword, treatment in treatment_keywords.items():
        if keyword in full_context_lower:
            booking_data['treatment'] = treatment
            break
    
    if 'treatment' not in booking_data:
        for msg in reversed(chat_history[-10:]):
            if msg.role == 'user':
                user_msg = msg.message.strip()
                user_lower = user_msg.lower()
                
                skip_keywords = ['yes', 'no', 'ok', 'okay', 'sure', 'dha', 'clifton', 
                               'fatima', 'ahmed', 'raza', 'confirm', 'correct', 'book',
                               'tomorrow', 'today', 'am', 'pm']
                
                if (len(user_msg) > 8 and 
                    not any(skip in user_lower for skip in skip_keywords) and
                    not re.search(r'\d{1,2}:\d{2}', user_msg) and
                    not re.search(r'\d{1,2}\s*(am|pm)', user_msg.lower()) and
                    not re.search(r'\b(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)', user_lower)):
                    booking_data['treatment'] = user_msg
                    break
    
    return booking_data

def extract_datetime_from_conversation(text: str, chat_history: List) -> Tuple[Optional[str], Optional[str]]:
    """Extract date and time from full conversation"""
    all_text = text
    if chat_history:
        recent = [msg.message for msg in chat_history[-10:]]
        all_text = ' '.join(recent) + ' ' + text
    
    date_str = parse_natural_date(all_text)
    time_str = parse_natural_time(all_text)
    
    return date_str, time_str

def check_appointment_conflict(user_id: int, appt_date: date, appt_time: time) -> bool:
    """Check if appointment slot is already booked"""
    session = get_session()
    try:
        existing = session.query(Appointment).filter(
            Appointment.user_id == user_id,
            Appointment.appointment_date == appt_date,
            Appointment.appointment_time == appt_time,
            Appointment.status == 'scheduled'
        ).first()
        return existing is not None
    finally:
        session.close()

def check_appointment_query(message: str) -> bool:
    """Check if user is asking about existing appointments"""
    message_lower = message.lower()
    
    booking_words = ['book', 'schedule', 'reserve', 'make appointment', 'want appointment']
    if any(word in message_lower for word in booking_words):
        return False
    
    query_keywords = [
        'my appointment', 'my appointments', 'show my appointment',
        'when is my appointment', 'check my appointment',
        'view my appointment', 'do i have appointment',
        'any upcoming appointment', 'what appointment do i have'
    ]
    
    return any(keyword in message_lower for keyword in query_keywords)

def get_user_appointments_info(user_id: int) -> str:
    """Get formatted string of user's upcoming appointments"""
    session = get_session()
    try:
        today = date.today()
        appointments = session.query(Appointment).filter(
            Appointment.user_id == user_id,
            Appointment.appointment_date >= today,
            Appointment.status == 'scheduled'
        ).order_by(Appointment.appointment_date, Appointment.appointment_time).all()
        
        if not appointments:
            return "You don't have any upcoming appointments scheduled. Would you like to book one?"
        
        response = f"You have {len(appointments)} upcoming appointment{'s' if len(appointments) > 1 else ''}:\n\n"
        
        for idx, appt in enumerate(appointments, 1):
            response += f"Appointment {idx}:\n"
            response += f"Date: {appt.appointment_date.strftime('%B %d, %Y')} ({appt.appointment_date.strftime('%A')})\n"
            response += f"Time: {appt.appointment_time.strftime('%I:%M %p')}\n"
            response += f"Branch: {appt.branch}\n"
            response += f"Dentist: {appt.dentist}\n"
            response += f"Treatment: {appt.treatment_type}\n"
            response += f"Status: {appt.status.capitalize()}\n"
            
            if idx < len(appointments):
                response += "\n---\n\n"
        
        response += "\nIf you need to reschedule or cancel any appointment, please let me know!"
        
        return response
    finally:
        session.close()

def handle_chat_message(user_id: int, message: str, session_id: Optional[int] = None) -> dict:
    """
    Handle chat message: save to DB, get bot response, handle appointments
    FIXED: Avoid validation loop by checking if booking is ready before validating
    """
    session = get_session()
    chatbot = get_rag_chatbot()
    
    try:
        # Create or get chat session
        if session_id:
            chat_session = session.query(ChatSession).filter(
                ChatSession.id == session_id,
                ChatSession.user_id == user_id
            ).first()
            
            if not chat_session:
                return {"success": False, "error": "Chat session not found"}
        else:
            session_title = chatbot.generate_session_title(message)
            chat_session = ChatSession(
                user_id=user_id,
                title=session_title,
                created_at=get_karachi_time()
            )
            session.add(chat_session)
            session.commit()
            session.refresh(chat_session)
        
        current_time = get_karachi_time()
        
        # Check for name extraction
        user_obj = session.query(User).filter(User.id == user_id).first()
        if not user_obj.full_name or user_obj.full_name.strip() == '':
            extracted_name = extract_name_from_message(message)
            if extracted_name:
                user_obj.full_name = extracted_name
                session.commit()
        
        # Save user message
        user_message = ChatMessage(
            session_id=chat_session.id,
            role="user",
            message=message,
            timestamp=current_time
        )
        session.add(user_message)
        session.commit()
        
        # Get recent messages for context
        recent_messages = session.query(ChatMessage).filter(
            ChatMessage.session_id == chat_session.id,
            ChatMessage.id != user_message.id
        ).order_by(ChatMessage.timestamp.desc()).limit(20).all()
        
        chat_history = [{"role": msg.role, "message": msg.message} for msg in reversed(recent_messages)]
        
        # Get user profile
        user_profile = get_user_profile_dict(user_id)
        
        # Check if asking about appointments
        if check_appointment_query(message):
            bot_response = get_user_appointments_info(user_id)
        else:
            # Check for booking data
            booking_data = parse_booking_data(message, list(reversed(recent_messages)))
            has_booking_data = len(booking_data) >= 2
            
            booking_keywords = ['book', 'confirm', 'schedule', 'appointment', 'yes', 'correct', 'all correct', 
                               'proceed', 'go ahead', 'thats right', "that's right", 'perfect']
            message_lower = message.lower().strip()
            has_booking_keyword = any(keyword in message_lower for keyword in booking_keywords)
            
            is_booking_request = has_booking_keyword or has_booking_data
            
            # FIXED: Only validate if ALL required fields are present
            if is_booking_request:
                required_fields = ['date', 'time', 'branch', 'dentist', 'treatment']
                missing_fields = [field for field in required_fields if field not in booking_data]
                
                if not missing_fields:
                    # All fields present - NOW validate
                    try:
                        appt_date = datetime.strptime(booking_data['date'], '%Y-%m-%d').date()
                        appt_time = datetime.strptime(booking_data['time'], '%H:%M').time()
                        
                        chatbot_instance = get_rag_chatbot()
                        date_valid, date_msg = chatbot_instance.validate_appointment_date(booking_data['date'])
                        time_valid, time_msg = chatbot_instance.validate_appointment_time(booking_data['time'], booking_data['date'])
                        
                        if not date_valid:
                            bot_response = date_msg
                        elif not time_valid:
                            bot_response = time_msg
                        elif check_appointment_conflict(user_id, appt_date, appt_time):
                            bot_response = "You already have an appointment at this time. Please choose a different slot."
                        else:
                            # Create appointment
                            appointment = Appointment(
                                user_id=user_id,
                                branch=booking_data['branch'],
                                dentist=booking_data['dentist'],
                                treatment_type=booking_data['treatment'],
                                appointment_date=appt_date,
                                appointment_time=appt_time,
                                status='scheduled',
                                created_at=current_time
                            )
                            session.add(appointment)
                            session.commit()
                            session.refresh(appointment)
                            
                            # Send confirmation email
                            user_name = user_obj.full_name or "Patient"
                            appointment_details = {
                                'date': booking_data['date'],
                                'time': booking_data['time'],
                                'branch': booking_data['branch'],
                                'dentist': booking_data['dentist'],
                                'treatment': booking_data['treatment']
                            }
                            
                            send_appointment_confirmation(user_obj.email, user_name, appointment_details)
                            
                            bot_response = f"""Perfect! Your appointment is confirmed.

Dear {user_name}, a confirmation email has been sent to {user_obj.email}.

Date: {booking_data['date']}
Time: {booking_data['time']}
Branch: {booking_data['branch']}
Dentist: {booking_data['dentist']}
Treatment: {booking_data['treatment']}

Please arrive 10 minutes early. See you soon!"""
                            
                    except Exception as e:
                        bot_response = f"There was an issue creating your appointment: {str(e)}. Please contact us at +92 300 1234567."
                else:
                    # Missing fields - let chatbot ask for them naturally
                    bot_response = chatbot.generate_response(
                        user_message=message,
                        chat_history=chat_history,
                        user_profile=user_profile
                    )
            else:
                # Regular conversation
                bot_response = chatbot.generate_response(
                    user_message=message,
                    chat_history=chat_history,
                    user_profile=user_profile
                )
        
        # Save bot message
        bot_message = ChatMessage(
            session_id=chat_session.id,
            role="bot",
            message=bot_response,
            timestamp=current_time
        )
        session.add(bot_message)
        
        if hasattr(chat_session, 'updated_at'):
            chat_session.updated_at = current_time
        
        session.commit()
        
        return {
            "success": True,
            "session_id": chat_session.id,
            "bot_response": bot_response,
            "timestamp": current_time.isoformat()
        }
        
    except Exception as e:
        session.rollback()
        return {"success": False, "error": str(e)}
    finally:
        session.close()