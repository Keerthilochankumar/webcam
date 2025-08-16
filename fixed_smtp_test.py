#!/usr/bin/env python3
"""
Fixed SMTP Test for MailerSend with proper email construction
"""

import smtplib
import base64
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# MailerSend SMTP Configuration
SMTP_SERVER = "smtp.mailersend.net"
SMTP_PORT = 2525
USERNAME = "MS_Is1Cd6@test-y7zpl980ey045vx6.mlsender.net"
PASSWORD = "mssp.uWR2neA.k68zxl2o0zmgj905.l8TlY4T"

def construct_message(message_text, to, sender, subject):
    """
    Construct email message using MIMEText
    """
    message = MIMEText(message_text)
    message['to'] = to
    message['from'] = sender
    message['subject'] = subject
    return message

def send_test_email():
    """
    Send test email using MailerSend SMTP
    """
    print("Starting SMTP Test...")
    
    # Email details
    sender = USERNAME
    to = "a9827400@gmail.com"
    subject = "Gmail Test - MailerSend SMTP Fixed"
    message_text = """Hello!

This is a test email sent using MailerSend SMTP service with fixed imports.

Configuration Details:
- Server: smtp.mailersend.net
- Port: 2025
- Authentication: Successful
- Import: Fixed MIMEText import issue

If you receive this email, the SMTP configuration is working correctly!

Best regards,
Fixed SMTP Test Script
"""
    
    print(f"Server: {SMTP_SERVER}:{SMTP_PORT}")
    print(f"From: {sender}")
    print(f"To: {to}")
    print(f"Subject: {subject}")
    print("-" * 50)
    
    try:
        # Construct message
        print("Constructing message...")
        message = construct_message(message_text, to, sender, subject)
        
        # Connect to SMTP server
        print("Connecting to SMTP server...")
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        
        print("Starting TLS...")
        server.starttls()
        
        print("Authenticating...")
        server.login(USERNAME, PASSWORD)
        
        print("Sending email...")
        server.send_message(message)
        server.quit()
        
        print("✅ SUCCESS: Email sent successfully!")
        print(f"📧 Email delivered to: {to}")
        return True
        
    except Exception as e:
        print(f"❌ ERROR: {e}")
        print(f"Error type: {type(e).__name__}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """
    Main function
    """
    success = send_test_email()
    
    if success:
        print("\n🎉 Test completed successfully!")
    else:
        print("\n💥 Test failed!")
    
    input("Press Enter to exit...")

if __name__ == "__main__":
    main()
