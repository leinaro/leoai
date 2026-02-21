
"""Handles retrieval of secrets from Google Cloud Secret Manager."""

import os
import logging
from typing import Optional, Dict
from google.cloud import secretmanager

# Simple in-memory cache to store secrets during the application's lifecycle
_cache: Dict[str, str] = {}

# Initialize the client outside of the function to reuse it
try:
    client = secretmanager.SecretManagerServiceClient()
    CLIENT_AVAILABLE = True
except Exception as e:
    logging.error(f"Could not initialize Secret Manager client: {e}. Secrets will not be available.")
    client = None
    CLIENT_AVAILABLE = False

def get_secret(secret_id: str, project_id: Optional[str] = None) -> Optional[str]:
    """
    Retrieves a secret from Google Cloud Secret Manager with in-memory caching.

    Args:
        secret_id: The ID of the secret to retrieve.
        project_id: The Google Cloud project ID. If not provided, it will be
                    inferred from the `GOOGLE_CLOUD_PROJECT` environment variable.

    Returns:
        The secret value as a string, or None if it cannot be retrieved.
    """
            
    logging.info("get secret with id "+secret_id)

    if not CLIENT_AVAILABLE:
        logging.warning("Secret Manager client is not available. Cannot fetch secret.")
        return None

    if secret_id in _cache:
        logging.info(f"Returning cached secret: {secret_id}")
        return _cache[secret_id]

    if not project_id:
        project_id = os.getenv("GOOGLE_CLOUD_PROJECT")

    if not project_id:
        logging.error("GOOGLE_CLOUD_PROJECT environment variable not set. Cannot fetch secret.")
        return None

    try:
        name = f"projects/{project_id}/secrets/{secret_id}/versions/latest"
        response = client.access_secret_version(request={"name": name})
        secret_value = response.payload.data.decode("UTF-8")
        
        _cache[secret_id] = secret_value  # Cache the secret
        logging.info(f"Successfully fetched and cached secret: {secret_id}")
        
        return secret_value
    except Exception as e:
        logging.error(f"Failed to access secret '{secret_id}': {e}")
        return None
