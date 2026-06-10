"""
Authentication service for secure password hashing and verification.
Uses PBKDF2 with SHA-256 from the standard Python library (no external dependencies required).
"""

import hashlib
import secrets

def hash_password(password: str) -> str:
    """
    Hash a password securely using PBKDF2-HMAC-SHA256.
    Generates a secure 16-byte hex salt and performs 100,000 iterations.
    """
    salt = secrets.token_hex(16)
    iterations = 100000
    pwd_bytes = password.encode('utf-8')
    salt_bytes = salt.encode('utf-8')
    
    hash_bytes = hashlib.pbkdf2_hmac('sha256', pwd_bytes, salt_bytes, iterations)
    hash_hex = hash_bytes.hex()
    
    # Format: iterations:salt:hash
    return f"{iterations}:{salt}:{hash_hex}"


def verify_password(password: str, password_hash: str) -> bool:
    """
    Verify a password against its secure hash.
    Uses secrets.compare_digest for constant-time comparison to prevent timing attacks.
    """
    try:
        parts = password_hash.split(':')
        if len(parts) != 3:
            return False
            
        iterations = int(parts[0])
        salt = parts[1]
        stored_hash = parts[2]
        
        pwd_bytes = password.encode('utf-8')
        salt_bytes = salt.encode('utf-8')
        
        hash_bytes = hashlib.pbkdf2_hmac('sha256', pwd_bytes, salt_bytes, iterations)
        hash_hex = hash_bytes.hex()
        
        # Constant-time comparison to block timing side-channel attacks
        return secrets.compare_digest(hash_hex, stored_hash)
    except Exception as e:
        print(f"[SECURITY ERROR] Password verification failed: {e}")
        return False
