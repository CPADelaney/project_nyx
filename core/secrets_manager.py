# core/secrets_manager.py

import os
import base64
import json
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import logging

logger = logging.getLogger("NYX-SecretsManager")

class SecretsManager:
    """Securely manages API keys and other sensitive credentials."""
    
    _instance = None
    
    def __new__(cls):
        """Singleton pattern to ensure only one instance exists."""
        if cls._instance is None:
            cls._instance = super(SecretsManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """Initialize the secrets manager."""
        if self._initialized:
            return
            
        self.secrets_file = "config/secrets.enc"
        self.salt_file = "config/salt"
        self.secrets = {}
        
        # Ensure the config directory exists
        os.makedirs("config", exist_ok=True)
        
        # Generate or load the salt
        self._load_or_generate_salt()
        
        # Initialize the encryption key
        self._initialize_encryption()
        
        # Load secrets if the file exists
        if os.path.exists(self.secrets_file):
            self._load_secrets()
        
        self._initialized = True
    
    def _load_or_generate_salt(self):
        """Load existing salt or generate a new one."""
        if os.path.exists(self.salt_file):
            with open(self.salt_file, "rb") as f:
                self.salt = f.read()
        else:
            # Generate a new salt
            import os
            self.salt = os.urandom(16)
            with open(self.salt_file, "wb") as f:
                f.write(self.salt)
    
    def _initialize_encryption(self):
        """Initialize the encryption system."""
        # Use a hardened password from the environment or a default
        password = os.environ.get("NYX_MASTER_PASSWORD", "nyx_default_password").encode()
        
        # Create a key derivation function
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=self.salt,
            iterations=100000,
        )
        
        # Derive a key from the password
        key = base64.urlsafe_b64encode(kdf.derive(password))
        self.cipher = Fernet(key)
    
    def _load_secrets(self):
        """Load and decrypt the secrets file."""
        try:
            with open(self.secrets_file, "rb") as f:
                encrypted_data = f.read()
            
            decrypted_data = self.cipher.decrypt(encrypted_data)
            self.secrets = json.loads(decrypted_data)
            
            logger.info("Secrets loaded successfully")
        except Exception as e:
            logger.error(f"Error loading secrets: {str(e)}")
            self.secrets = {}
    
    def _save_secrets(self):
        """Encrypt and save the secrets file."""
        try:
            encrypted_data = self.cipher.encrypt(json.dumps(self.secrets).encode())
            
            with open(self.secrets_file, "wb") as f:
                f.write(encrypted_data)
                
            logger.info("Secrets saved successfully")
            return True
        except Exception as e:
            logger.error(f"Error saving secrets: {str(e)}")
            return False
    
    def get_secret(self, key, default=None):
        """Get a secret by key with an optional default value."""
        # First check if the secret is in our stored secrets
        if key in self.secrets:
            return self.secrets[key]
        
        # Then check if it's an environment variable
        env_value = os.environ.get(key)
        if env_value:
            # Store for future use (optional, comment out if not desired)
            self.set_secret(key, env_value)
            return env_value
        
        return default
    
    def set_secret(self, key, value):
        """Set a secret value and save the secrets file."""
        self.secrets[key] = value
        return self._save_secrets()
    
    def delete_secret(self, key):
        """Delete a secret if it exists."""
        if key in self.secrets:
            del self.secrets[key]
            return self._save_secrets()
        return True
    
    def rotate_encryption_key(self, new_password):
        """Rotate the encryption key using a new password."""
        # Save the current secrets
        current_secrets = self.secrets.copy()
        
        # Update the password in the environment
        os.environ["NYX_MASTER_PASSWORD"] = new_password
        
        # Re-initialize encryption with the new password
        self._initialize_encryption()
        
        # Update the secrets dictionary
        self.secrets = current_secrets
        
        # Save with the new encryption
        return self._save_secrets()

# Global instance
secrets_manager = SecretsManager()

def get_secret(key, default=None):
    """Global function to get a secret."""
    return secrets_manager.get_secret(key, default)

def set_secret(key, value):
    """Global function to set a secret."""
    return secrets_manager.set_secret(key, value)

# Example usage:
if __name__ == "__main__":
    # Set a secret (in a real project, this would be done in a setup script, not in the module itself)
    if "OPENAI_API_KEY" in os.environ:
        set_secret("OPENAI_API_KEY", os.environ["OPENAI_API_KEY"])
        print("API key stored securely")
    
    # Get a secret
    api_key = get_secret("OPENAI_API_KEY", "default_key")
    print(f"Got API key: {api_key[:5]}...")  # Only print the first few characters for security
