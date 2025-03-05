# core/auth/middleware.py

import os
import time
import hmac
import hashlib
import logging
import functools
import secrets
from flask import request, jsonify
from datetime import datetime, timedelta
import uuid
from typing import Dict, Callable, Any, Optional

logger = logging.getLogger("NYX-AuthMiddleware")

# Either load the API key from environment or generate a secure one
API_KEY = os.environ.get('NYX_API_KEY') or secrets.token_hex(32)
# Store active sessions with expiration time
ACTIVE_SESSIONS: Dict[str, datetime] = {}
# Session expiration time (30 minutes)
SESSION_EXPIRY = timedelta(minutes=30)

def generate_token(username: str) -> str:
    """
    Generates a secure authentication token.
    
    Args:
        username (str): The username to associate with the token
        
    Returns:
        str: The generated token
    """
    timestamp = str(int(time.time()))
    token_uuid = str(uuid.uuid4())
    message = f"{username}:{timestamp}:{token_uuid}"
    
    # Create HMAC signature using the API key
    signature = hmac.new(
        API_KEY.encode('utf-8'),
        message.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    
    # The final token is username:timestamp:uuid:signature
    token = f"{message}:{signature}"
    
    # Store the session with expiration time
    ACTIVE_SESSIONS[token] = datetime.now() + SESSION_EXPIRY
    
    return token

def verify_token(token: str) -> bool:
    """
    Verifies an authentication token.
    
    Args:
        token (str): The token to verify
        
    Returns:
        bool: True if the token is valid, False otherwise
    """
    try:
        # Check if the token exists and is not expired
        if token in ACTIVE_SESSIONS:
            if datetime.now() > ACTIVE_SESSIONS[token]:
                # Token expired, remove it
                del ACTIVE_SESSIONS[token]
                return False
            
            # Extend session expiration
            ACTIVE_SESSIONS[token] = datetime.now() + SESSION_EXPIRY
            
            # Split the token
            parts = token.split(':')
            if len(parts) != 4:
                return False
                
            username, timestamp, token_uuid, signature = parts
            
            # Recreate the message
            message = f"{username}:{timestamp}:{token_uuid}"
            
            # Verify the signature
            expected_signature = hmac.new(
                API_KEY.encode('utf-8'),
                message.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()
            
            return hmac.compare_digest(signature, expected_signature)
        return False
    except Exception as e:
        logger.error(f"Error verifying token: {str(e)}")
        return False

def invalidate_token(token: str) -> bool:
    """
    Invalidates an authentication token (logout).
    
    Args:
        token (str): The token to invalidate
        
    Returns:
        bool: True if the token was invalidated, False otherwise
    """
    if token in ACTIVE_SESSIONS:
        del ACTIVE_SESSIONS[token]
        return True
    return False

def cleanup_expired_sessions() -> None:
    """Removes expired sessions from memory."""
    now = datetime.now()
    expired_tokens = [token for token, expiry in ACTIVE_SESSIONS.items() if now > expiry]
    for token in expired_tokens:
        del ACTIVE_SESSIONS[token]
    
    if expired_tokens:
        logger.info(f"Cleaned up {len(expired_tokens)} expired sessions")

def api_key_auth_required(f: Callable) -> Callable:
    """
    Decorator to enforce API key authentication for API endpoints.
    
    Args:
        f (Callable): The function to decorate
        
    Returns:
        Callable: The decorated function
    """
    @functools.wraps(f)
    def decorated(*args: Any, **kwargs: Any) -> Any:
        # Get the API key from the request
        api_key = request.headers.get('X-API-Key')
        
        # Verify the API key
        if not api_key or api_key != API_KEY:
            return jsonify({'error': 'Unauthorized'}), 401
            
        return f(*args, **kwargs)
    return decorated

def token_auth_required(f: Callable) -> Callable:
    """
    Decorator to enforce token authentication for API endpoints.
    
    Args:
        f (Callable): The function to decorate
        
    Returns:
        Callable: The decorated function
    """
    @functools.wraps(f)
    def decorated(*args: Any, **kwargs: Any) -> Any:
        # Get the authentication token from the request
        auth_header = request.headers.get('Authorization')
        
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'error': 'Unauthorized'}), 401
            
        token = auth_header[7:]  # Remove 'Bearer ' prefix
        
        # Verify the token
        if not verify_token(token):
            return jsonify({'error': 'Invalid or expired token'}), 401
            
        # Clean up expired sessions occasionally
        if random.random() < 0.1:  # 10% chance to clean up
            cleanup_expired_sessions()
            
        return f(*args, **kwargs)
    return decorated

# For backwards compatibility, a simple API key helper
def get_api_key() -> str:
    """
    Returns the current API key.
    
    Returns:
        str: The API key
    """
    return API_KEY

# Helper function to print the API key during startup (for development only)
def print_api_key() -> None:
    """Prints the API key to the console."""
    logger.info(f"API Key: {API_KEY}")
    logger.info("Store this key securely for API authentication.")

# Example authentication functions for the API
def authenticate(username: str, password: str) -> Optional[str]:
    """
    Authenticates a user and returns a token.
    
    Args:
        username (str): The username
        password (str): The password
        
    Returns:
        str or None: The authentication token if successful, None otherwise
    """
    # In a real application, this would validate against a user database
    # For this example, we'll use a hardcoded username/password
    if username == "admin" and password == "nyx_secure_password":
        return generate_token(username)
    return None

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    print_api_key()
