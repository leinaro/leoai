"""Handles interactions with the AI service (Gemini)."""

import logging
import os

import google.genai as genai

# Configure the generative AI model
try:
    genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
    model = genai.GenerativeModel('gemini-pro')
except Exception as e:
    logging.error(f"Failed to configure Gemini: {e}")
    model = None

def get_gemini_response(text: str) -> str | None:
    """Generates a response from the Gemini model.

    Args:
        text: The input text to the model.

    Returns:
        The generated response, or None if an error occurred.
    """
    if not model:
        logging.error("Gemini model is not available.")
        return None

    try:
        response = model.generate_content(text)
        # Assuming the response format has a 'text' attribute or similar
        # You might need to adjust this based on the actual response object
        return response.text
    except Exception as e:
        logging.error(f"Error generating response from Gemini: {e}")
        return None
