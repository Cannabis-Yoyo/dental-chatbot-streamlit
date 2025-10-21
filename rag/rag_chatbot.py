"""
Enhanced RAG Chatbot with Smart Booking & Name Recognition
"""
import os
import json
from typing import List, Dict, Optional
from datetime import datetime, date, time, timedelta
from sentence_transformers import SentenceTransformer
import faiss
import numpy as np
from groq import Groq
import re

class RAGChatbot:
    def __init__(self, knowledge_base_path: str, groq_api_key: str):
        self.groq_client = Groq(api_key=groq_api_key)
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        self.knowledge_base = self._load_knowledge_base(knowledge_base_path)
        self.chunks = self._create_chunks()
        self.index = self._build_faiss_index()
        self.system_prompt = self._create_system_prompt()
    
    def _load_knowledge_base(self, path: str) -> dict:
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {"treatments": {}, "faqs": [], "clinic_info": {}}
    
    def _create_chunks(self) -> List[Dict[str, str]]:
        chunks = []
        
        # Treatment chunks
        for treatment_key, treatment in self.knowledge_base.get('treatments', {}).items():
            chunk_text = f"Treatment: {treatment['title']}\n"
            chunk_text += f"Description: {treatment['description']}\n"
            chunk_text += f"Indications: {', '.join(treatment.get('indications', []))}\n"
            chunk_text += f"Procedure: {' '.join(treatment.get('procedure_steps', []))}"
            chunks.append({'text': chunk_text, 'metadata': {'type': 'treatment', 'name': treatment_key}})
            
            if 'aftercare_and_home_instructions' in treatment:
                aftercare_text = f"{treatment['title']} - Aftercare:\n" + '\n'.join(treatment['aftercare_and_home_instructions'])
                chunks.append({'text': aftercare_text, 'metadata': {'type': 'treatment', 'name': treatment_key}})
        
        # FAQ chunks
        for faq in self.knowledge_base.get('faqs', []):
            faq_text = f"Q: {faq['question']}\nA: {faq['answer']}"
            chunks.append({'text': faq_text, 'metadata': {'type': 'faq'}})
        
        # Clinic info chunks
        clinic_info = self.knowledge_base.get('clinic_info', {})
        for branch in clinic_info.get('branches', []):
            branch_text = f"Branch: {branch['name']}\nAddress: {branch['address']}\nPhone: {branch['phone']}\nHours: {json.dumps(branch.get('hours', {}))}"
            chunks.append({'text': branch_text, 'metadata': {'type': 'clinic', 'branch_name': branch['name']}})
        
        return chunks
    
    def _build_faiss_index(self):
        if not self.chunks:
            return faiss.IndexFlatL2(384)
        texts = [chunk['text'] for chunk in self.chunks]
        embeddings = self.embedding_model.encode(texts, convert_to_numpy=True)
        dimension = embeddings.shape[1]
        index = faiss.IndexFlatL2(dimension)
        index.add(embeddings.astype('float32'))
        return index
    
    def _create_system_prompt(self) -> str:
        return """You are a helpful dental assistant at NeoImplant Dental Studio.

CRITICAL NAME RULES:
1. Check patient context FIRST before asking anything
2. If patient name IS SET → Use it naturally in conversation, NEVER ask for it again
3. If patient name NOT SET → Ask ONCE: "Hello! What's your name?"
4. NEVER repeat questions - check context first

APPOINTMENT BOOKING:
- When user provides booking details (date, time, branch, dentist, treatment) → System will AUTOMATICALLY book it
- You DON'T need to ask "would you like to book?" - just acknowledge their information
- Only ask for MISSING information one at a time
- Be conversational and helpful

Example flow:
User: "book appointment 23 Oct 11 AM Dr Fatima DHA for cleaning"
You: "Got it! I'm booking you for October 23rd at 11 AM with Dr. Fatima at our DHA branch for teeth cleaning."
→ System handles the rest automatically

NEVER:
- Don't ask "would you like to book?" when they already said book
- Don't repeat questions that were already answered
- Don't ask for name if patient context shows it's already set
- Don't be pushy or overly formal

Be natural, warm, helpful, and conversational. Think of yourself as a friendly receptionist."""

    def _retrieve_context(self, query: str, top_k: int = 3) -> str:
        if not self.chunks:
            return "No context available."
        try:
            query_embedding = self.embedding_model.encode([query], convert_to_numpy=True)
            distances, indices = self.index.search(query_embedding.astype('float32'), top_k)
            relevant_chunks = [self.chunks[idx]['text'] for idx in indices[0] if idx < len(self.chunks)]
            return "\n\n---\n\n".join(relevant_chunks)
        except:
            return "Error retrieving context."
    
    def _format_chat_history(self, messages: List[Dict[str, str]]) -> str:
        if not messages:
            return "This is the FIRST message from patient."
        
        formatted = "CONVERSATION HISTORY:\n"
        for msg in messages[-10:]:  # Last 10 messages for context
            role = "Patient" if msg['role'] == 'user' else "You"
            formatted += f"{role}: {msg['message']}\n"
        return formatted
    
    def _create_patient_context(self, user_profile: Optional[Dict] = None) -> str:
        """Create patient context with clear instructions about name"""
        if not user_profile:
            return "Patient: Unknown - Ask name once\n"
        
        name = user_profile.get('full_name', '').strip()
        
        if name:
            # Name IS SET - use it, DON'T ask again
            context = f"Patient Name: {name} ⚠️ NAME ALREADY SET - USE IT NATURALLY, DO NOT ASK FOR IT AGAIN\n"
        else:
            # Name NOT SET - ask once
            context = "Patient Name: NOT SET ⚠️ Ask once: 'Hello! What's your name?'\n"
        
        # Add clinical info if available
        clinical = user_profile.get('clinical_info', {})
        if clinical:
            if clinical.get('current_dental_issues') and clinical['current_dental_issues'] != 'None':
                context += f"Known Issue: {clinical['current_dental_issues']}\n"
            if clinical.get('allergies') and clinical['allergies'] != 'None':
                context += f"⚠️ Allergies: {clinical['allergies']}\n"
            if clinical.get('past_dental_procedures') and clinical['past_dental_procedures'] != 'None':
                context += f"Past Procedures: {clinical['past_dental_procedures']}\n"
        
        return context
    
    def extract_booking_intent(self, message: str) -> bool:
        """Check if user wants to book appointment"""
        booking_keywords = ['book', 'appointment', 'schedule', 'reserve', 'visit', 'consultation']
        return any(keyword in message.lower() for keyword in booking_keywords)
    
    def get_available_branches(self) -> List[str]:
        """Get branch names from knowledge base"""
        branches = self.knowledge_base.get('clinic_info', {}).get('branches', [])
        return [b['name'] for b in branches]
    
    def get_available_dentists(self) -> List[str]:
        """Get dentist names from knowledge base"""
        team = self.knowledge_base.get('clinic_info', {}).get('team', [])
        return [f"Dr. {t['name']}" for t in team]
    
    def validate_appointment_date(self, date_str: str) -> tuple:
        """Validate if date is valid for appointment - FIXED"""
        try:
            appt_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            today = date.today()
            
            # FIXED: Changed from <= to < (allow future dates, not today or past)
            if appt_date < today:
                return False, "Please choose a future date (not past dates)."
            
            # Allow today if it's still business hours, otherwise it will be caught by time validation
            
            weekday = appt_date.strftime('%A').lower()
            if weekday == 'sunday':
                return False, "We're closed on Sundays. Please choose another day."
            
            return True, "Valid date"
        except:
            return False, "Invalid date format. Use YYYY-MM-DD"
    
    def validate_appointment_time(self, time_str: str, date_str: str) -> tuple:
        """Validate if time is within working hours"""
        try:
            appt_time = datetime.strptime(time_str, '%H:%M').time()
            appt_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            weekday = appt_date.strftime('%A').lower()
            
            branches = self.knowledge_base.get('clinic_info', {}).get('branches', [])
            if branches:
                hours = branches[0].get('hours', {}).get(weekday, "Closed")
                if hours == "Closed":
                    return False, f"Clinic is closed on {weekday.capitalize()}"
                
                start, end = hours.split('-')
                start_time = datetime.strptime(start, '%H:%M').time()
                end_time = datetime.strptime(end, '%H:%M').time()
                
                if not (start_time <= appt_time < end_time):
                    return False, f"Please choose time between {start} and {end}"
            
            if appt_time.minute != 0:
                return False, "Appointments are on the hour (e.g., 10:00, 11:00, 14:00)"
            
            return True, "Valid time"
        except:
            return False, "Invalid time format. Use HH:MM (e.g., 14:00)"
    
    def generate_response(
        self, 
        user_message: str, 
        chat_history: List[Dict[str, str]] = None,
        user_profile: Optional[Dict] = None
    ) -> str:
        """Generate chatbot response using RAG"""
        
        # Get relevant knowledge base context
        kb_context = self._retrieve_context(user_message, top_k=2)
        
        # Create patient context
        patient_context = self._create_patient_context(user_profile)
        
        # Format chat history
        history_text = self._format_chat_history(chat_history)
        
        # Build full prompt
        full_prompt = f"""{patient_context}

{history_text}

Knowledge Base Context:
{kb_context}

Patient's Latest Message: {user_message}

Respond naturally and helpfully. Remember to check patient context before asking questions:"""
        
        try:
            response = self.groq_client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": full_prompt}
                ],
                temperature=0.7,
                max_tokens=400
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"[GROQ ERROR] {e}")
            return "Sorry, I'm having a technical issue. Please call us at +92 300 1234567 for immediate assistance."
    
    def generate_session_title(self, first_message: str) -> str:
        """Generate a short title for chat session"""
        try:
            response = self.groq_client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": "Generate a 3-5 word title. No quotes."},
                    {"role": "user", "content": f"Message: {first_message}"}
                ],
                temperature=0.5,
                max_tokens=15
            )
            title = response.choices[0].message.content.strip().strip('"\'')
            return title[:50]
        except:
            words = first_message.split()[:4]
            return ' '.join(words).capitalize() if words else "New Chat"