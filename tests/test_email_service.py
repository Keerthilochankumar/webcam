"""
Unit tests for EmailService
"""
import unittest
import tempfile
import os
from datetime import datetime
from unittest.mock import MagicMock, patch, mock_open
from pathlib import Path

from managers.email_service import EmailService


class TestEmailService(unittest.TestCase):
    """Test cases for EmailService"""
    
    def setUp(self):
        """Set up test environment"""
        self.email_service = EmailService()
    
    def test_init(self):
        """Test EmailService initialization"""
        self.assertIsNone(self.email_service.smtp_server)
        self.assertEqual(self.email_service.smtp_port, 587)  # DEFAULT_SMTP_PORT
        self.assertIsNone(self.email_service.username)
        self.assertIsNone(self.email_service.password)
        self.assertIsNone(self.email_service.from_email)
        self.assertEqual(len(self.email_service.to_emails), 0)
        self.assertTrue(self.email_service.use_tls)
        self.assertFalse(self.email_service.is_configured)
    
    @patch.object(EmailService, '_test_smtp_connection')
    def test_configure_smtp_success(self, mock_test_connection):
        """Test successful SMTP configuration"""
        mock_test_connection.return_value = True
        
        result = self.email_service.configure_smtp(
            server="smtp.gmail.com",
            port=587,
            username="test@gmail.com",
            password="testpassword"
        )
        
        self.assertTrue(result)
        self.assertTrue(self.email_service.is_configured)
        self.assertEqual(self.email_service.smtp_server, "smtp.gmail.com")
        self.assertEqual(self.email_service.smtp_port, 587)
        self.assertEqual(self.email_service.username, "test@gmail.com")
        self.assertEqual(self.email_service.from_email, "test@gmail.com")
        mock_test_connection.assert_called_once()
    
    @patch.object(EmailService, '_test_smtp_connection')
    def test_configure_smtp_test_fails(self, mock_test_connection):
        """Test SMTP configuration when connection test fails"""
        mock_test_connection.return_value = False
        
        result = self.email_service.configure_smtp(
            server="smtp.gmail.com",
            port=587,
            username="test@gmail.com",
            password="testpassword"
        )
        
        self.assertFalse(result)
        self.assertFalse(self.email_service.is_configured)
    
    def test_configure_smtp_with_custom_from_email(self):
        """Test SMTP configuration with custom from email"""
        with patch.object(self.email_service, '_test_smtp_connection', return_value=True):
            result = self.email_service.configure_smtp(
                server="smtp.gmail.com",
                port=587,
                username="test@gmail.com",
                password="testpassword",
                from_email="noreply@example.com"
            )
        
        self.assertTrue(result)
        self.assertEqual(self.email_service.from_email, "noreply@example.com")
    
    def test_add_recipient_valid_email(self):
        """Test adding valid email recipient"""
        result = self.email_service.add_recipient("test@example.com")
        
        self.assertTrue(result)
        self.assertIn("test@example.com", self.email_service.to_emails)
    
    def test_add_recipient_invalid_email(self):
        """Test adding invalid email recipient"""
        result = self.email_service.add_recipient("invalid-email")
        
        self.assertFalse(result)
        self.assertNotIn("invalid-email", self.email_service.to_emails)
    
    def test_add_recipient_duplicate(self):
        """Test adding duplicate email recipient"""
        self.email_service.add_recipient("test@example.com")
        result = self.email_service.add_recipient("test@example.com")
        
        self.assertTrue(result)
        self.assertEqual(self.email_service.to_emails.count("test@example.com"), 1)
    
    def test_remove_recipient_exists(self):
        """Test removing existing email recipient"""
        self.email_service.add_recipient("test@example.com")
        result = self.email_service.remove_recipient("test@example.com")
        
        self.assertTrue(result)
        self.assertNotIn("test@example.com", self.email_service.to_emails)
    
    def test_remove_recipient_not_exists(self):
        """Test removing non-existent email recipient"""
        result = self.email_service.remove_recipient("nonexistent@example.com")
        
        self.assertFalse(result)
    
    @patch.object(EmailService, '_send_email_with_attachment')
    @patch('pathlib.Path.exists')
    def test_send_intrusion_alert_with_attachment(self, mock_exists, mock_send_with_attachment):
        """Test sending intrusion alert with attachment"""
        # Configure email service
        self.email_service.is_configured = True
        self.email_service.add_recipient("admin@example.com")
        
        mock_exists.return_value = True
        mock_send_with_attachment.return_value = True
        
        timestamp = datetime.now()
        media_path = "/path/to/intrusion_video.avi"
        
        result = self.email_service.send_intrusion_alert(timestamp, media_path)
        
        self.assertTrue(result)
        mock_send_with_attachment.assert_called_once()
    
    @patch.object(EmailService, '_send_email')
    @patch('pathlib.Path.exists')
    def test_send_intrusion_alert_without_attachment(self, mock_exists, mock_send_email):
        """Test sending intrusion alert without attachment (file doesn't exist)"""
        # Configure email service
        self.email_service.is_configured = True
        self.email_service.add_recipient("admin@example.com")
        
        mock_exists.return_value = False
        mock_send_email.return_value = True
        
        timestamp = datetime.now()
        media_path = "/path/to/nonexistent_video.avi"
        
        result = self.email_service.send_intrusion_alert(timestamp, media_path)
        
        self.assertTrue(result)
        mock_send_email.assert_called_once()
    
    def test_send_intrusion_alert_not_configured(self):
        """Test sending intrusion alert when not configured"""
        timestamp = datetime.now()
        media_path = "/path/to/intrusion_video.avi"
        
        result = self.email_service.send_intrusion_alert(timestamp, media_path)
        
        self.assertFalse(result)
    
    def test_send_intrusion_alert_no_recipients(self):
        """Test sending intrusion alert with no recipients"""
        self.email_service.is_configured = True
        
        timestamp = datetime.now()
        media_path = "/path/to/intrusion_video.avi"
        
        result = self.email_service.send_intrusion_alert(timestamp, media_path)
        
        self.assertFalse(result)
    
    @patch.object(EmailService, '_send_email')
    def test_send_system_alert(self, mock_send_email):
        """Test sending system alert"""
        # Configure email service
        self.email_service.is_configured = True
        self.email_service.add_recipient("admin@example.com")
        
        mock_send_email.return_value = True
        
        result = self.email_service.send_system_alert("SYSTEM_ERROR", "Test error message")
        
        self.assertTrue(result)
        mock_send_email.assert_called_once()
        
        # Check that subject and body were created correctly
        call_args = mock_send_email.call_args
        subject = call_args[0][0]
        body = call_args[0][1]
        
        self.assertIn("SYSTEM_ERROR", subject)
        self.assertIn("Test error message", body)
    
    @patch.object(EmailService, '_send_email')
    def test_send_test_email(self, mock_send_email):
        """Test sending test email"""
        # Configure email service
        self.email_service.is_configured = True
        self.email_service.add_recipient("admin@example.com")
        
        mock_send_email.return_value = True
        
        result = self.email_service.send_test_email()
        
        self.assertTrue(result)
        mock_send_email.assert_called_once()
        
        # Check that it's a test email
        call_args = mock_send_email.call_args
        subject = call_args[0][0]
        body = call_args[0][1]
        
        self.assertIn("Test Email", subject)
        self.assertIn("test email", body)
    
    @patch('smtplib.SMTP')
    def test_send_message_success(self, mock_smtp):
        """Test successful message sending"""
        # Configure email service
        self.email_service.is_configured = True
        self.email_service.smtp_server = "smtp.gmail.com"
        self.email_service.smtp_port = 587
        self.email_service.username = "test@gmail.com"
        self.email_service.password = "testpassword"
        self.email_service.from_email = "test@gmail.com"
        self.email_service.use_tls = True
        self.email_service.add_recipient("admin@example.com")
        
        # Mock SMTP server
        mock_server = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_server
        
        result = self.email_service._send_email("Test Subject", "Test Body")
        
        self.assertTrue(result)
        mock_server.starttls.assert_called_once()
        mock_server.login.assert_called_once_with("test@gmail.com", "testpassword")
        mock_server.send_message.assert_called_once()
    
    @patch('smtplib.SMTP')
    def test_send_message_auth_failure(self, mock_smtp):
        """Test message sending with authentication failure"""
        # Configure email service
        self.email_service.is_configured = True
        self.email_service.smtp_server = "smtp.gmail.com"
        self.email_service.smtp_port = 587
        self.email_service.username = "test@gmail.com"
        self.email_service.password = "wrongpassword"
        self.email_service.from_email = "test@gmail.com"
        self.email_service.add_recipient("admin@example.com")
        
        # Mock SMTP authentication error
        mock_server = MagicMock()
        mock_server.login.side_effect = smtplib.SMTPAuthenticationError(535, "Authentication failed")
        mock_smtp.return_value.__enter__.return_value = mock_server
        
        result = self.email_service._send_email("Test Subject", "Test Body")
        
        self.assertFalse(result)
    
    @patch('smtplib.SMTP')
    def test_test_smtp_connection_success(self, mock_smtp):
        """Test successful SMTP connection test"""
        self.email_service.smtp_server = "smtp.gmail.com"
        self.email_service.smtp_port = 587
        self.email_service.username = "test@gmail.com"
        self.email_service.password = "testpassword"
        self.email_service.use_tls = True
        
        # Mock successful connection
        mock_server = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_server
        
        result = self.email_service._test_smtp_connection()
        
        self.assertTrue(result)
        mock_server.starttls.assert_called_once()
        mock_server.login.assert_called_once()
    
    @patch('smtplib.SMTP')
    def test_test_smtp_connection_failure(self, mock_smtp):
        """Test SMTP connection test failure"""
        self.email_service.smtp_server = "smtp.gmail.com"
        self.email_service.smtp_port = 587
        self.email_service.username = "test@gmail.com"
        self.email_service.password = "wrongpassword"
        
        # Mock connection failure
        mock_smtp.side_effect = smtplib.SMTPConnectError(421, "Service not available")
        
        result = self.email_service._test_smtp_connection()
        
        self.assertFalse(result)
    
    def test_validate_email_valid(self):
        """Test email validation with valid emails"""
        valid_emails = [
            "test@example.com",
            "user.name@domain.co.uk",
            "user+tag@example.org",
            "123@example.com"
        ]
        
        for email in valid_emails:
            with self.subTest(email=email):
                self.assertTrue(self.email_service._validate_email(email))
    
    def test_validate_email_invalid(self):
        """Test email validation with invalid emails"""
        invalid_emails = [
            "invalid-email",
            "@example.com",
            "test@",
            "test.example.com",
            "test@.com",
            ""
        ]
        
        for email in invalid_emails:
            with self.subTest(email=email):
                self.assertFalse(self.email_service._validate_email(email))
    
    def test_get_configuration_status(self):
        """Test getting configuration status"""
        # Initially not configured
        status = self.email_service.get_configuration_status()
        self.assertFalse(status['is_configured'])
        self.assertEqual(status['recipient_count'], 0)
        
        # Configure and test again
        with patch.object(self.email_service, '_test_smtp_connection', return_value=True):
            self.email_service.configure_smtp("smtp.gmail.com", 587, "test@gmail.com", "password")
            self.email_service.add_recipient("admin@example.com")
        
        status = self.email_service.get_configuration_status()
        self.assertTrue(status['is_configured'])
        self.assertEqual(status['smtp_server'], "smtp.gmail.com")
        self.assertEqual(status['recipient_count'], 1)
        self.assertIn("admin@example.com", status['recipients'])
    
    def test_clear_configuration(self):
        """Test clearing configuration"""
        # Configure first
        with patch.object(self.email_service, '_test_smtp_connection', return_value=True):
            self.email_service.configure_smtp("smtp.gmail.com", 587, "test@gmail.com", "password")
            self.email_service.add_recipient("admin@example.com")
        
        # Clear configuration
        self.email_service.clear_configuration()
        
        # Verify everything is cleared
        self.assertFalse(self.email_service.is_configured)
        self.assertIsNone(self.email_service.smtp_server)
        self.assertIsNone(self.email_service.username)
        self.assertEqual(len(self.email_service.to_emails), 0)
    
    def test_create_intrusion_alert_body(self):
        """Test creating intrusion alert email body"""
        timestamp = datetime(2023, 1, 1, 12, 0, 0)
        media_path = "/path/to/intrusion_video.avi"
        additional_details = "Multiple failed login attempts"
        
        body = self.email_service._create_intrusion_alert_body(timestamp, media_path, additional_details)
        
        self.assertIn("SECURITY ALERT", body)
        self.assertIn("2023-01-01 12:00:00", body)
        self.assertIn("intrusion_video.avi", body)
        self.assertIn("Multiple failed login attempts", body)
        self.assertIn("Evidence has been automatically captured", body)
    
    @patch('builtins.open', new_callable=mock_open, read_data=b"fake video data")
    @patch('pathlib.Path.exists')
    @patch.object(EmailService, '_send_message')
    def test_send_email_with_attachment(self, mock_send_message, mock_exists, mock_file):
        """Test sending email with attachment"""
        # Configure email service
        self.email_service.from_email = "test@example.com"
        self.email_service.to_emails = ["admin@example.com"]
        
        mock_exists.return_value = True
        mock_send_message.return_value = True
        
        result = self.email_service._send_email_with_attachment(
            "Test Subject", 
            "Test Body", 
            "/path/to/attachment.avi"
        )
        
        self.assertTrue(result)
        mock_send_message.assert_called_once()


if __name__ == '__main__':
    # Import smtplib for exception testing
    import smtplib
    unittest.main()