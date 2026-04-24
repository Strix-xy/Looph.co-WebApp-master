"""
Field-level encryption for sensitive data at rest.
Uses Fernet (symmetric) with key from environment FIELD_ENCRYPTION_KEY.
"""
import os

def _get_fernet():
    key = os.environ.get('FIELD_ENCRYPTION_KEY')
    if not key or len(key) != 44:
        return None
    try:
        from cryptography.fernet import Fernet
        return Fernet(key.encode() if isinstance(key, str) else key)
    except Exception:
        return None


def encrypt_field(plaintext):
    """Encrypt a string for storage. Returns plaintext if encryption unavailable."""
    if plaintext is None or (isinstance(plaintext, str) and not plaintext.strip()):
        return plaintext
    f = _get_fernet()
    if not f:
        return plaintext
    try:
        return f.encrypt(plaintext.encode('utf-8')).decode('ascii')
    except Exception:
        return plaintext


def decrypt_field(ciphertext):
    """Decrypt a stored string. Returns ciphertext if decryption unavailable or not encrypted."""
    if ciphertext is None or (isinstance(ciphertext, str) and not ciphertext.strip()):
        return ciphertext
    f = _get_fernet()
    if not f:
        return ciphertext
    try:
        return f.decrypt(ciphertext.encode('ascii')).decode('utf-8')
    except Exception:
        return ciphertext
