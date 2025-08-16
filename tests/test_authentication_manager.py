"""
Unit tests for AuthenticationManager
"""
import unittest
import tempfile
import os

from managers.authentication_manager import AuthenticationManager
from database.database_manager import DatabaseManager


class TestAuthenticationManager(unittest.TestCase):
    """Test cases for AuthenticationManager"""
    
    def setUp(self):
        """Set up test environment"""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        self.db_manager = DatabaseManager(self.temp_db.name)
        self.auth_manager = AuthenticationManager(self.db_manager)
    
    def tearDown(self):
        """Clean up test environment"""
        self.db_manager.close()
        os.unlink(self.temp_db.name)
    
    def test_hash_password(self):
        """Test password hashing"""
        password = "testpassword123"
        hash1 = self.auth_manager.hash_password(password)
        hash2 = self.auth_manager.hash_password(password)
        
        # Hashes should be different due to random salt
        self.assertNotEqual(hash1, hash2)
        
        # Hash should be hex string of expected length
        # Salt (32 bytes = 64 hex chars) + SHA-256 hash (64 hex chars) = 128 chars
        self.assertEqual(len(hash1), 128)
        self.assertEqual(len(hash2), 128)
    
    def test_verify_password(self):
        """Test password verification"""
        password = "testpassword123"
        password_hash = self.auth_manager.hash_password(password)
        
        # Correct password should verify
        self.assertTrue(self.auth_manager.verify_password(password, password_hash))
        
        # Wrong password should not verify
        self.assertFalse(self.auth_manager.verify_password("wrongpassword", password_hash))
    
    def test_setup_initial_password(self):
        """Test initial password setup"""
        username = "testuser"
        password = "testpassword123"
        
        # First setup should succeed
        result = self.auth_manager.setup_initial_password(username, password)
        self.assertTrue(result)
        
        # Second setup with same username should fail
        result = self.auth_manager.setup_initial_password(username, "anotherpassword")
        self.assertFalse(result)
    
    def test_authenticate_user(self):
        """Test user authentication"""
        username = "testuser"
        password = "testpassword123"
        
        # Setup user
        self.auth_manager.setup_initial_password(username, password)
        
        # Correct credentials should authenticate
        result = self.auth_manager.authenticate_user(username, password)
        self.assertTrue(result)
        self.assertTrue(self.auth_manager.is_authenticated())
        self.assertEqual(self.auth_manager.get_current_user().username, username)
        
        # Wrong password should fail
        result = self.auth_manager.authenticate_user(username, "wrongpassword")
        self.assertFalse(result)
        
        # Non-existent user should fail
        result = self.auth_manager.authenticate_user("nonexistent", password)
        self.assertFalse(result)
    
    def test_logout_user(self):
        """Test user logout"""
        username = "testuser"
        password = "testpassword123"
        
        # Setup and authenticate user
        self.auth_manager.setup_initial_password(username, password)
        self.auth_manager.authenticate_user(username, password)
        self.assertTrue(self.auth_manager.is_authenticated())
        
        # Logout
        self.auth_manager.logout_user()
        self.assertFalse(self.auth_manager.is_authenticated())
        self.assertIsNone(self.auth_manager.get_current_user())
    
    def test_validate_password_strength(self):
        """Test password strength validation"""
        # Weak passwords
        weak_passwords = [
            "123",  # Too short
            "password",  # No uppercase, no digits
            "PASSWORD",  # No lowercase, no digits
            "Password",  # No digits
            "Password1"  # This should actually pass
        ]
        
        for password in weak_passwords[:-1]:  # Exclude the last one
            is_valid, message = self.auth_manager.validate_password_strength(password)
            self.assertFalse(is_valid)
            self.assertIsInstance(message, str)
        
        # Strong password
        is_valid, message = self.auth_manager.validate_password_strength("Password123")
        self.assertTrue(is_valid)
        self.assertEqual(message, "Password is strong")
    
    def test_has_users(self):
        """Test checking if users exist"""
        # Initially no users
        self.assertFalse(self.auth_manager.has_users())
        
        # After creating user
        self.auth_manager.setup_initial_password("testuser", "testpassword123")
        self.assertTrue(self.auth_manager.has_users())
    
    def test_password_with_special_characters(self):
        """Test password handling with special characters"""
        password = "Test@Pass123!#$"
        password_hash = self.auth_manager.hash_password(password)
        
        # Should verify correctly
        self.assertTrue(self.auth_manager.verify_password(password, password_hash))
        
        # Should work with authentication
        username = "testuser"
        self.auth_manager.setup_initial_password(username, password)
        result = self.auth_manager.authenticate_user(username, password)
        self.assertTrue(result)
    
    def test_empty_password(self):
        """Test handling of empty password"""
        password_hash = self.auth_manager.hash_password("")
        self.assertTrue(self.auth_manager.verify_password("", password_hash))
        self.assertFalse(self.auth_manager.verify_password("nonempty", password_hash))


if __name__ == '__main__':
    unittest.main()