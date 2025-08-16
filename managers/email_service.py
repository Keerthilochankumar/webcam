"""
Email service for Camera Privacy Manager
Handles SMTP configuration, email notifications, and alert delivery
"""
import smtplib
import logging
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from typing import Optional, List
from pathlib import Path

from config import DEFAULT_SMTP_PORT, EMAIL_TIMEOUT


class EmailService:
    """Manages email notifications and SMTP operations"""
    
    def __init__(self):
        """Initialize email service"""
        self.logger = logging.getLogger(__name__)
        self.smtp_server = None
        self.smtp_port = DEFAULT_SMTP_PORT
        self.username = None
        self.password = None
        self.from_email = None
        self.to_emails = []
        self.use_tls = True
        self.is_configured = False
    
    def configure_smtp(self, server: str, port: int, username: str, password: str, 
                      from_email: str = None, use_tls: bool = True) -> bool:
        """
        Configure SMTP settings
        
        Args:
            server: SMTP server hostname
            port: SMTP server port
            username: SMTP username
            password: SMTP password
            from_email: From email address (defaults to username)
            use_tls: Whether to use TLS encryption
            
        Returns:
            True if configuration successful, False otherwise
        """
        try:
            self.smtp_server = server
            self.smtp_port = port
            self.username = username
            self.password = password
            self.from_email = from_email or username
            self.use_tls = use_tls
            
            # Test the configuration
            if self._test_smtp_connection():
                self.is_configured = True
                self.logger.info(f"SMTP configured successfully for server: {server}")
                return True
            else:
                self.is_configured = False
                self.logger.error("SMTP configuration test failed")
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to configure SMTP: {e}")
            self.is_configured = False
            return False
    
    def add_recipient(self, email: str) -> bool:
        """
        Add email recipient
        
        Args:
            email: Email address to add
            
        Returns:
            True if added successfully, False otherwise
        """
        try:
            if self._validate_email(email):
                if email not in self.to_emails:
                    self.to_emails.append(email)
                    self.logger.info(f"Added email recipient: {email}")
                return True
            else:
                self.logger.error(f"Invalid email address: {email}")
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to add recipient: {e}")
            return False
    
    def remove_recipient(self, email: str) -> bool:
        """
        Remove email recipient
        
        Args:
            email: Email address to remove
            
        Returns:
            True if removed successfully, False otherwise
        """
        try:
            if email in self.to_emails:
                self.to_emails.remove(email)
                self.logger.info(f"Removed email recipient: {email}")
                return True
            else:
                self.logger.warning(f"Email recipient not found: {email}")
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to remove recipient: {e}")
            return False
    
    def send_intrusion_alert(self, timestamp: datetime, media_path: str, 
                           additional_details: str = None) -> bool:
        """
        Send intrusion alert email
        
        Args:
            timestamp: Timestamp of the intrusion attempt
            media_path: Path to captured media file
            additional_details: Optional additional details
            
        Returns:
            True if email sent successfully, False otherwise
        """
        try:
            if not self.is_configured:
                self.logger.error("Email service not configured")
                return False
            
            if not self.to_emails:
                self.logger.error("No email recipients configured")
                return False
            
            # Create email content
            subject = f"SECURITY ALERT: Unauthorized Access Attempt Detected"
            
            body = self._create_intrusion_alert_body(timestamp, media_path, additional_details)
            
            # Send email with attachment if media file exists
            if Path(media_path).exists():
                return self._send_email_with_attachment(subject, body, media_path)
            else:
                return self._send_email(subject, body)
                
        except Exception as e:
            self.logger.error(f"Failed to send intrusion alert: {e}")
            return False
    
    def send_system_alert(self, alert_type: str, message: str, timestamp: datetime = None) -> bool:
        """
        Send general system alert email
        
        Args:
            alert_type: Type of alert (e.g., "SYSTEM_ERROR", "ADMIN_ACCESS")
            message: Alert message
            timestamp: Optional timestamp
            
        Returns:
            True if email sent successfully, False otherwise
        """
        try:
            if not self.is_configured:
                self.logger.error("Email service not configured")
                return False
            
            if not self.to_emails:
                self.logger.error("No email recipients configured")
                return False
            
            if timestamp is None:
                timestamp = datetime.now()
            
            subject = f"Camera Privacy Manager Alert: {alert_type}"
            
            body = f"""
Camera Privacy Manager System Alert

Alert Type: {alert_type}
Timestamp: {timestamp.strftime('%Y-%m-%d %H:%M:%S')}

Message:
{message}

This is an automated alert from your Camera Privacy Manager system.
Please review your system logs for additional details.

---
Camera Privacy Manager
            """.strip()
            
            return self._send_email(subject, body)
            
        except Exception as e:
            self.logger.error(f"Failed to send system alert: {e}")
            return False
    
    def send_test_email(self) -> bool:
        """
        Send test email to verify configuration
        
        Returns:
            True if test email sent successfully, False otherwise
        """
        try:
            if not self.is_configured:
                self.logger.error("Email service not configured")
                return False
            
            if not self.to_emails:
                self.logger.error("No email recipients configured")
                return False
            
            subject = "Camera Privacy Manager - Test Email"
            body = f"""
This is a test email from your Camera Privacy Manager system.

Configuration Details:
- SMTP Server: {self.smtp_server}:{self.smtp_port}
- From Email: {self.from_email}
- TLS Enabled: {self.use_tls}
- Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

If you received this email, your email notification system is working correctly.

---
Camera Privacy Manager
            """.strip()
            
            result = self._send_email(subject, body)
            if result:
                self.logger.info("Test email sent successfully")
            return result
            
        except Exception as e:
            self.logger.error(f"Failed to send test email: {e}")
            return False
    
    def _create_intrusion_alert_body(self, timestamp: datetime, media_path: str, 
                                   additional_details: str = None) -> str:
        """Create intrusion alert email body"""
        body = f"""
SECURITY ALERT: Unauthorized Access Attempt Detected

An unauthorized access attempt has been detected on your Camera Privacy Manager system.

Incident Details:
- Timestamp: {timestamp.strftime('%Y-%m-%d %H:%M:%S')}
- Evidence File: {Path(media_path).name}
- File Path: {media_path}
"""
        
        if additional_details:
            body += f"- Additional Details: {additional_details}\n"
        
        body += """
Actions Taken:
- Evidence has been automatically captured and stored
- Incident has been logged in the system
- This alert has been sent to configured recipients

Recommended Actions:
1. Review the captured evidence file
2. Check system logs for additional details
3. Verify physical security of your system
4. Consider changing system passwords if necessary

This is an automated security alert from your Camera Privacy Manager system.
Please investigate this incident promptly.

---
Camera Privacy Manager Security System
        """.strip()
        
        return body
    
    def _send_email(self, subject: str, body: str) -> bool:
        """Send plain text email"""
        try:
            msg = MIMEText(body)
            msg['Subject'] = subject
            msg['From'] = self.from_email
            msg['To'] = ', '.join(self.to_emails)
            
            return self._send_message(msg)
            
        except Exception as e:
            self.logger.error(f"Failed to create email message: {e}")
            return False
    
    def _send_email_with_attachment(self, subject: str, body: str, attachment_path: str) -> bool:
        """Send email with attachment"""
        try:
            msg = MIMEMultipart()
            msg['Subject'] = subject
            msg['From'] = self.from_email
            msg['To'] = ', '.join(self.to_emails)
            
            # Add body
            msg.attach(MIMEText(body, 'plain'))
            
            # Add attachment
            if Path(attachment_path).exists():
                with open(attachment_path, 'rb') as attachment:
                    part = MIMEBase('application', 'octet-stream')
                    part.set_payload(attachment.read())
                
                encoders.encode_base64(part)
                part.add_header(
                    'Content-Disposition',
                    f'attachment; filename= {Path(attachment_path).name}'
                )
                msg.attach(part)
            else:
                self.logger.warning(f"Attachment file not found: {attachment_path}")
            
            return self._send_message(msg)
            
        except Exception as e:
            self.logger.error(f"Failed to create email with attachment: {e}")
            return False
    
    def _send_message(self, msg) -> bool:
        """Send email message via SMTP"""
        try:
            with smtplib.SMTP(self.smtp_server, self.smtp_port, timeout=EMAIL_TIMEOUT) as server:
                if self.use_tls:
                    server.starttls()
                
                server.login(self.username, self.password)
                server.send_message(msg)
                
            self.logger.info(f"Email sent successfully to {len(self.to_emails)} recipients")
            return True
            
        except smtplib.SMTPAuthenticationError as e:
            self.logger.error(f"SMTP authentication failed: {e}")
            return False
        except smtplib.SMTPConnectError as e:
            self.logger.error(f"SMTP connection failed: {e}")
            return False
        except smtplib.SMTPException as e:
            self.logger.error(f"SMTP error: {e}")
            return False
        except Exception as e:
            self.logger.error(f"Failed to send email: {e}")
            return False
    
    def _test_smtp_connection(self) -> bool:
        """Test SMTP connection and authentication"""
        try:
            with smtplib.SMTP(self.smtp_server, self.smtp_port, timeout=EMAIL_TIMEOUT) as server:
                if self.use_tls:
                    server.starttls()
                
                server.login(self.username, self.password)
                
            self.logger.info("SMTP connection test successful")
            return True
            
        except smtplib.SMTPAuthenticationError as e:
            self.logger.error(f"SMTP authentication test failed: {e}")
            return False
        except smtplib.SMTPConnectError as e:
            self.logger.error(f"SMTP connection test failed: {e}")
            return False
        except Exception as e:
            self.logger.error(f"SMTP test failed: {e}")
            return False
    
    def _validate_email(self, email: str) -> bool:
        """Validate email address format"""
        import re
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    def get_configuration_status(self) -> dict:
        """
        Get current configuration status
        
        Returns:
            Dictionary containing configuration details
        """
        return {
            'is_configured': self.is_configured,
            'smtp_server': self.smtp_server,
            'smtp_port': self.smtp_port,
            'from_email': self.from_email,
            'recipient_count': len(self.to_emails),
            'recipients': self.to_emails.copy(),
            'use_tls': self.use_tls
        }
    
    def clear_configuration(self) -> None:
        """Clear all configuration settings"""
        self.smtp_server = None
        self.smtp_port = DEFAULT_SMTP_PORT
        self.username = None
        self.password = None
        self.from_email = None
        self.to_emails.clear()
        self.use_tls = True
        self.is_configured = False
        self.logger.info("Email configuration cleared")