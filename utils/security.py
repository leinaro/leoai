"""Utility functions for security purposes."""

import hashlib
import hmac
from typing import Optional

def validate_whatsapp_signature(request_body: bytes, signature: Optional[str], secret: str) -> bool:
    """Validates the X-Hub-Signature-256 header from WhatsApp.

    Args:
        request_body: The raw request body from WhatsApp.
        signature: The value of the X-Hub-Signature-256 header.
        secret: Your WhatsApp App Secret.

    Returns:
        True if the signature is valid, False otherwise.
    """
    if not signature:
        return False

    expected_signature = "sha256=" + hmac.new(
        secret.encode("utf-8"), request_body, hashlib.sha256
    ).hexdigest()

    return hmac.compare_digest(expected_signature, signature)
