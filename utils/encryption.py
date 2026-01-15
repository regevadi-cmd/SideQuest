"""Encryption utilities for securing sensitive data like API keys."""
import os
import base64
import logging
from typing import Optional

logger = logging.getLogger(__name__)

# Check if cryptography is available
try:
    from cryptography.fernet import Fernet, InvalidToken
    ENCRYPTION_AVAILABLE = True
except ImportError:
    ENCRYPTION_AVAILABLE = False
    logger.warning("cryptography package not installed. API key encryption disabled.")


def get_encryption_key() -> Optional[bytes]:
    """Get the encryption key from environment.

    Returns:
        Encryption key as bytes, or None if not configured
    """
    key = os.getenv("ENCRYPTION_KEY")
    if not key:
        return None
    try:
        # Key should be a valid Fernet key (base64-encoded 32 bytes)
        return key.encode()
    except Exception as e:
        logger.error(f"Invalid encryption key format: {e}")
        return None


def generate_encryption_key() -> str:
    """Generate a new Fernet encryption key.

    Returns:
        Base64-encoded encryption key string
    """
    if not ENCRYPTION_AVAILABLE:
        raise RuntimeError("cryptography package required for encryption")
    return Fernet.generate_key().decode()


def encrypt_value(value: str) -> Optional[str]:
    """Encrypt a string value.

    Args:
        value: Plain text value to encrypt

    Returns:
        Base64-encoded encrypted value, or None if encryption fails
    """
    if not ENCRYPTION_AVAILABLE:
        logger.warning("Encryption not available, storing value in plain text")
        return value

    key = get_encryption_key()
    if not key:
        logger.warning("No encryption key configured, storing value in plain text")
        return value

    try:
        f = Fernet(key)
        encrypted = f.encrypt(value.encode())
        return encrypted.decode()
    except Exception as e:
        logger.error(f"Encryption failed: {e}")
        return None


def decrypt_value(encrypted_value: str) -> Optional[str]:
    """Decrypt an encrypted string value.

    Args:
        encrypted_value: Base64-encoded encrypted value

    Returns:
        Decrypted plain text value, or None if decryption fails
    """
    if not ENCRYPTION_AVAILABLE:
        # If encryption isn't available, assume value is plain text
        return encrypted_value

    key = get_encryption_key()
    if not key:
        # No encryption key - value might be plain text from before encryption was enabled
        return encrypted_value

    try:
        f = Fernet(key)
        decrypted = f.decrypt(encrypted_value.encode())
        return decrypted.decode()
    except InvalidToken:
        # Value might be plain text (not encrypted)
        logger.debug("Value appears to be plain text (not encrypted)")
        return encrypted_value
    except Exception as e:
        logger.error(f"Decryption failed: {e}")
        return None


def is_encrypted(value: str) -> bool:
    """Check if a value appears to be Fernet-encrypted.

    Args:
        value: Value to check

    Returns:
        True if value appears to be encrypted
    """
    if not value:
        return False
    try:
        # Fernet tokens start with 'gAAAAA'
        return value.startswith('gAAAAA') and len(value) > 100
    except Exception:
        return False


def mask_api_key(key: str, visible_chars: int = 8) -> str:
    """Mask an API key for display purposes.

    Args:
        key: API key to mask
        visible_chars: Number of characters to show at start

    Returns:
        Masked key like 'sk-ant-a3****'
    """
    if not key:
        return ""
    if len(key) <= visible_chars:
        return "*" * len(key)
    return key[:visible_chars] + "*" * 8
