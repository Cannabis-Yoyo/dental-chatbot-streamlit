"""
Helper utilities module
Email sending, verification codes, etc.
"""
import streamlit as st
import smtplib
import random
import string
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def generate_verification_code(length=6) -> str:
    """Generate random verification code"""
    return ''.join(random.choices(string.digits, k=length))

def send_verification_email(to_email: str, code: str) -> bool:
    """Send verification email"""
    try:
        message = MIMEMultipart()
        message["From"] = st.secrets['SMTP_FROM']
        message["To"] = to_email
        message["Subject"] = "Dental Care - Email Verification"
        
        body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; padding: 20px;">
            <h2 style="color: #5B9FED;">Welcome to Dental Care</h2>
            <p>Your verification code is:</p>
            <h1 style="color: #5B9FED; letter-spacing: 5px;">{code}</h1>
            <p>This code will expire in 10 minutes.</p>
            <p>If you didn't request this code, please ignore this email.</p>
        </body>
        </html>
        """
        
        message.attach(MIMEText(body, "html"))
        
        server = smtplib.SMTP(st.secrets['SMTP_HOST'], int(st.secrets['SMTP_PORT']))
        server.starttls()
        server.login(st.secrets['SMTP_USER'], st.secrets['SMTP_PASSWORD'])
        server.send_message(message)
        server.quit()
        
        return True
    except Exception as e:
        print(f"Error sending email: {e}")
        return False

def send_appointment_confirmation(to_email: str, user_name: str, appointment_details: dict) -> bool:
    """Send appointment confirmation email"""
    try:
        message = MIMEMultipart()
        message["From"] = st.secrets['SMTP_FROM']
        message["To"] = to_email
        message["Subject"] = "Appointment Confirmation - NeoImplant Dental Studio"
        
        body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; padding: 20px; background-color: #f4f4f4;">
            <div style="max-width: 600px; margin: 0 auto; background-color: white; padding: 30px; border-radius: 10px;">
                <h2 style="color: #5B9FED; text-align: center;">🦷 Appointment Confirmed</h2>
                <p style="font-size: 16px;">Dear <strong>{user_name}</strong>,</p>
                <p>Your appointment has been successfully scheduled at <strong>NeoImplant Dental Studio</strong>.</p>
                
                <div style="background-color: #f8f9fa; padding: 20px; border-radius: 8px; margin: 20px 0;">
                    <h3 style="color: #333; margin-top: 0;">Appointment Details:</h3>
                    <table style="width: 100%; border-collapse: collapse;">
                        <tr>
                            <td style="padding: 8px 0; color: #666;"><strong>Date:</strong></td>
                            <td style="padding: 8px 0; color: #333;">{appointment_details['date']}</td>
                        </tr>
                        <tr>
                            <td style="padding: 8px 0; color: #666;"><strong>Time:</strong></td>
                            <td style="padding: 8px 0; color: #333;">{appointment_details['time']}</td>
                        </tr>
                        <tr>
                            <td style="padding: 8px 0; color: #666;"><strong>Branch:</strong></td>
                            <td style="padding: 8px 0; color: #333;">{appointment_details['branch']}</td>
                        </tr>
                        <tr>
                            <td style="padding: 8px 0; color: #666;"><strong>Dentist:</strong></td>
                            <td style="padding: 8px 0; color: #333;">{appointment_details['dentist']}</td>
                        </tr>
                        <tr>
                            <td style="padding: 8px 0; color: #666;"><strong>Treatment:</strong></td>
                            <td style="padding: 8px 0; color: #333;">{appointment_details['treatment']}</td>
                        </tr>
                    </table>
                </div>
                
                <p style="font-size: 14px; color: #666;">Please arrive 10 minutes before your scheduled time.</p>
                <p style="font-size: 14px; color: #666;">If you need to reschedule, please contact us at least 24 hours in advance.</p>
                
                <div style="text-align: center; margin-top: 30px; padding-top: 20px; border-top: 1px solid #e0e0e0;">
                    <p style="color: #666; font-size: 13px;">NeoImplant Dental Studio</p>
                    <p style="color: #666; font-size: 13px;">Contact: +92 300 1234567</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        message.attach(MIMEText(body, "html"))
        
        server = smtplib.SMTP(st.secrets['SMTP_HOST'], int(st.secrets['SMTP_PORT']))
        server.starttls()
        server.login(st.secrets['SMTP_USER'], st.secrets['SMTP_PASSWORD'])
        server.send_message(message)
        server.quit()
        
        return True
    except Exception as e:
        print(f"Error sending appointment email: {e}")
        return False