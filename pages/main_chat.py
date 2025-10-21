"""
Main Chat Interface with RAG Chatbot - FIXED VERSION
"""
import streamlit as st
from datetime import datetime
import html
from utils.db import get_session, ChatSession, ChatMessage, get_karachi_time, get_user_profile_dict
from utils.auth import logout
from utils.chatbot import handle_chat_message

# Styling
st.markdown("""
<style>
.stApp { 
    background: #0f1419; 
    font-family: "Inter", sans-serif; 
}

/* HIDE DEFAULT STREAMLIT SIDEBAR NAVIGATION */
[data-testid="stSidebarNav"] {
    display: none !important;
}

/* Sidebar styling */
[data-testid="stSidebar"] {
    background: #1a1a1a !important;
}

[data-testid="stSidebar"] > div:first-child {
    background: #1a1a1a !important;
}

/* IMPROVED MESSAGE STYLING - ChatGPT Style */
.message-container {
    display: flex;
    margin-bottom: 24px;
    width: 100%;
    clear: both;
}

.message-user { 
    justify-content: flex-end;
}

.message-bot { 
    justify-content: flex-start;
}

.message-bubble {
    max-width: 65%;
    padding: 12px 16px;
    border-radius: 18px;
    line-height: 1.5;
    font-size: 15px;
    word-wrap: break-word;
    position: relative;
}

.bubble-user { 
    background: #2563eb; 
    color: #ffffff;
    border-bottom-right-radius: 4px;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.3);
}

.bubble-bot { 
    background: #2d2d2d; 
    color: #ececec;
    border: 1px solid #3d3d3d;
    border-bottom-left-radius: 4px;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.3);
}

.message-time { 
    font-size: 11px; 
    color: rgba(255, 255, 255, 0.6); 
    margin-top: 6px; 
    font-weight: 400;
}

.typing-indicator { 
    display: flex; 
    align-items: center; 
    gap: 6px; 
    padding: 12px 20px; 
    background: #2d2d2d;
    border: 1px solid #3d3d3d;
    border-radius: 18px; 
    max-width: 80px;
    border-bottom-left-radius: 4px;
}

.typing-dot { 
    width: 8px; 
    height: 8px; 
    border-radius: 50%; 
    background: #6b7280; 
    animation: typing 1.4s infinite; 
}

.typing-dot:nth-child(2) { animation-delay: 0.2s; }
.typing-dot:nth-child(3) { animation-delay: 0.4s; }

@keyframes typing { 
    0%, 60%, 100% { transform: translateY(0); opacity: 0.5; } 
    30% { transform: translateY(-8px); opacity: 1; } 
}

.stButton>button {
    background: #2563eb !important;
    color: white !important;
    border: none !important;
    border-radius: 8px !important;
    font-weight: 500 !important;
}

.stButton>button:hover {
    background: #1d4ed8 !important;
}

.stTextInput>div>div>input {
    background: #1a1a1a !important;
    border: 1px solid #374151 !important;
    color: #ffffff !important;
    border-radius: 8px !important;
}

.stTextInput>div>div>input:focus {
    border-color: #2563eb !important;
    box-shadow: 0 0 0 1px #2563eb !important;
}
</style>
""", unsafe_allow_html=True)

hide_nav = """
<style>
/* Hide the default Streamlit page navigation links */
[data-testid="stSidebarNav"] {
    display: none !important;
}

/* Optional: adjust sidebar padding after hiding nav */
section[data-testid="stSidebar"] > div:first-child {
    padding-top: 1rem;
}
</style>
"""

st.markdown(hide_nav, unsafe_allow_html=True)

def show():
    """Main function to display chat interface"""
    
    # Initialize session state
    if 'current_session_id' not in st.session_state:
        st.session_state.current_session_id = None
    if 'chat_sessions' not in st.session_state:
        st.session_state.chat_sessions = []
    if 'current_messages' not in st.session_state:
        st.session_state.current_messages = []
    if 'waiting_for_response' not in st.session_state:
        st.session_state.waiting_for_response = False
    
    # Render sidebar
    render_sidebar()
    
    # Render main chat area
    render_chat_area()

def render_sidebar():
    """Render sidebar with chat history"""
    with st.sidebar:
        st.markdown("### 🦷 Dental Care")
        st.markdown("---")
        
        if st.button("➕ New Chat", use_container_width=True, key="new_chat_btn"):
            start_new_chat()
        
        st.markdown("---")
        
        # Load sessions if not already loaded
        if not st.session_state.chat_sessions:
            load_chat_sessions()
        
        if st.session_state.chat_sessions:
            st.markdown("#### 💬 Chat History")
            
            for session in st.session_state.chat_sessions:
                is_active = st.session_state.current_session_id == session['id']
                button_type = "primary" if is_active else "secondary"
                
                # Truncate title to fit
                title_display = session['title'][:30] + "..." if len(session['title']) > 30 else session['title']
                
                if st.button(
                    title_display,
                    key=f"session_{session['id']}",
                    use_container_width=True,
                    type=button_type
                ):
                    load_session_messages(session['id'])
        else:
            st.info("No chat history yet")

def render_chat_area():
    """Render main chat area"""
    col1, col2 = st.columns([6, 1])
    
    with col1:
        st.title("💬 Dental Care Assistant")
    
    with col2:
        profile_action = st.selectbox(
            "",
            ["👤 Profile", "⚙️ Settings", "🚪 Sign Out"],
            key="profile_menu",
            label_visibility="collapsed"
        )
        
        if profile_action == "⚙️ Settings":
            st.session_state.show_settings = True
            st.rerun()
        elif profile_action == "🚪 Sign Out":
            logout()
            st.rerun()
    
    st.markdown("---")
    
    # Display messages
    render_messages()
    
    # Chat input
    render_chat_input()

def render_messages():
    """Render chat messages with improved styling"""
    chat_container = st.container()
    
    with chat_container:
        if not st.session_state.current_messages:
            st.markdown("""
            <div style='text-align: center; padding: 80px 20px; color: #6b7280;'>
                <div style='font-size: 64px; margin-bottom: 20px;'>🦷</div>
                <h2 style='color: #ffffff; margin-bottom: 10px;'>Welcome to Dental Care Assistant</h2>
                <p style='font-size: 16px;'>How can I assist you with your dental care today?</p>
            </div>
            """, unsafe_allow_html=True)
        else:
            for msg in st.session_state.current_messages:
                is_user = msg['role'] == 'user'
                time_str = format_timestamp(msg.get('timestamp', ''))
                safe_msg = html.escape(str(msg.get('message', ''))).replace('\n', '<br/>')
                
                if is_user:
                    # User message - right aligned
                    st.markdown(f"""
                    <div style='display: flex; justify-content: flex-end; margin-bottom: 24px;'>
                        <div style='max-width: 65%; padding: 12px 16px; border-radius: 18px; background: #2563eb; color: #ffffff; border-bottom-right-radius: 4px; box-shadow: 0 1px 3px rgba(0, 0, 0, 0.3);'>
                            {safe_msg}
                            <div style='font-size: 11px; color: rgba(255, 255, 255, 0.7); margin-top: 6px;'>{time_str}</div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    # Bot message - left aligned
                    st.markdown(f"""
                    <div style='display: flex; justify-content: flex-start; margin-bottom: 24px;'>
                        <div style='max-width: 65%; padding: 12px 16px; border-radius: 18px; background: #2d2d2d; color: #ececec; border: 1px solid #3d3d3d; border-bottom-left-radius: 4px; box-shadow: 0 1px 3px rgba(0, 0, 0, 0.3);'>
                            {safe_msg}
                            <div style='font-size: 11px; color: rgba(255, 255, 255, 0.6); margin-top: 6px;'>{time_str}</div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
        
        if st.session_state.waiting_for_response:
            st.markdown("""
            <div style='display: flex; justify-content: flex-start; margin-bottom: 24px;'>
                <div style='display: flex; align-items: center; gap: 6px; padding: 12px 20px; background: #2d2d2d; border: 1px solid #3d3d3d; border-radius: 18px; max-width: 80px; border-bottom-left-radius: 4px;'>
                    <div class='typing-dot'></div>
                    <div class='typing-dot'></div>
                    <div class='typing-dot'></div>
                </div>
            </div>
            """, unsafe_allow_html=True)

def render_chat_input():
    """Render chat input form"""
    with st.form(key="chat_form", clear_on_submit=True):
        col1, col2 = st.columns([5, 1])
        
        with col1:
            user_input = st.text_input(
                "",
                placeholder="Type your message here...",
                key="user_input",
                disabled=st.session_state.waiting_for_response,
                label_visibility="collapsed"
            )
        
        with col2:
            submitted = st.form_submit_button(
                "Send",
                disabled=st.session_state.waiting_for_response,
                use_container_width=True
            )
        
        if submitted and user_input and user_input.strip():
            send_message(user_input)
            st.rerun()
    
    # Handle bot response
    if st.session_state.waiting_for_response:
        get_bot_response()
        st.rerun()

def format_timestamp(timestamp_str: str) -> str:
    """Format timestamp for display"""
    try:
        dt = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        return dt.strftime("%I:%M %p")
    except:
        return ""

def load_chat_sessions():
    """Load chat history from database"""
    session = get_session()
    try:
        sessions = session.query(ChatSession).filter(
            ChatSession.user_id == st.session_state.user_id
        ).order_by(ChatSession.created_at.desc()).all()
        
        st.session_state.chat_sessions = [
            {
                "id": s.id,
                "title": s.title,
                "created_at": s.created_at.isoformat(),
                "updated_at": s.updated_at.isoformat() if hasattr(s, 'updated_at') else s.created_at.isoformat()
            }
            for s in sessions
        ]
    finally:
        session.close()

def load_session_messages(session_id: int):
    """Load messages for a specific session"""
    session = get_session()
    try:
        messages = session.query(ChatMessage).filter(
            ChatMessage.session_id == session_id
        ).order_by(ChatMessage.timestamp.asc()).all()
        
        st.session_state.current_messages = [
            {
                'role': msg.role,
                'message': msg.message,
                'timestamp': msg.timestamp.isoformat()
            }
            for msg in messages
        ]
        st.session_state.current_session_id = session_id
    finally:
        session.close()

def start_new_chat():
    """Start a new chat session"""
    st.session_state.current_session_id = None
    st.session_state.current_messages = []

def send_message(message: str):
    """Add user message to chat"""
    if not message or not message.strip() or st.session_state.waiting_for_response:
        return
    
    user_msg = {
        'role': 'user',
        'message': message.strip(),
        'timestamp': datetime.now().isoformat()
    }
    st.session_state.current_messages.append(user_msg)
    st.session_state.waiting_for_response = True

def get_bot_response():
    """Get bot response and save to database"""
    if st.session_state.waiting_for_response and st.session_state.current_messages:
        last_msg = st.session_state.current_messages[-1]
        if last_msg['role'] == 'user':
            # Handle chat message
            result = handle_chat_message(
                st.session_state.user_id,
                last_msg['message'],
                st.session_state.current_session_id
            )
            
            if result['success']:
                st.session_state.current_session_id = result['session_id']
                bot_msg = {
                    'role': 'bot',
                    'message': result['bot_response'],
                    'timestamp': result['timestamp']
                }
                st.session_state.current_messages.append(bot_msg)
                load_chat_sessions()
            else:
                st.error(f"Error: {result.get('error')}")
            
            st.session_state.waiting_for_response = False