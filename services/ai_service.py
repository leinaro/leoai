"""Handles interactions with the Google Generative AI (Gemini)."""

import logging
import os
import google.generativeai as genai
from typing import Dict, Any


def get_gemini_response(text: str) -> Dict[str, Any]:
    """Parses text into a structured JSON using Gemini.

    Args:
        text: The text to parse.

    Returns:
        A dictionary with the parsed data (Concept, Amount, Category),
        or an empty dictionary if an error occurs.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        logging.error("GEMINI_API_KEY not found in environment variables.")
        return {}

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-pro')

    prompt = f"""Extract the concept, amount, and category from the following text. 
    Return the result in a JSON format with the keys 'Concept', 'Amount', and 'Category'.
    Text: {text}
    """

    try:
        response = model.generate_content(prompt)
        # Clean up the response to get a valid JSON
        cleaned_response = response.text.strip().replace('```json', '').replace('```', '')
        return eval(cleaned_response)  # Use eval carefully, consider json.loads for production
    except Exception as e:
        logging.error(f"Error getting Gemini response: {e}")
        return {}
