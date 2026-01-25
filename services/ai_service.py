"""Handles all interactions with the Gemini AI model."""

import os
import logging
from typing import Optional

from google import genai
from google.genai import types

# --- Gemini AI Model Initialization ---

def initialize_gemini():
    """Initializes and returns the Gemini client.
    
    Returns:
        A configured Client instance or None if initialization fails.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    
    if not api_key:
        logging.error("GEMINI_API_KEY not found in environment variables. The model cannot be initialized.")
        return None

    logging.info("GEMINI_API_KEY found. Configuring Gemini...")
    
    try:
        client = genai.Client(api_key=api_key)
        logging.info("Gemini client initialized successfully.")
        return client
    except Exception as e:
        logging.error(f"An error occurred during Gemini client initialization: {e}")
        return None

# --- Main Service Logic ---

def process_with_gemini(client, text: str, image_bytes: Optional[bytes] = None) -> Optional[str]:
    """Processes the given text and/or image using the Gemini model."""
    if not client:
        logging.error("Cannot process content because the Gemini client is not available.")
        return None
    
    try:
        system_instruction = (
            "Act as a Senior Financial Assistant. From the user's message and/or image, extract financial transaction data "
            "and return it as a JSON object with fields: "
            "{'concept': str, 'amount': float, 'category': str, 'currency': str, 'date': str, 'folder': str}. "
            "Analyze the image (like a receipt or invoice) to find details. Use the text for context. "
            "Folder rules: MUST be one of ['Salitre', 'Tramonte', 'Villa', 'Manuela Sancho']. Infer the folder from context. If uncertain, use 'Unknown'. "
            "- If the folder cannot be confidently determined, set 'folder' to 'Unknown'. "
            "Category rules: "
            "- Assign the most appropriate category based on the nature of the expense or income. "
            "- Use only predefined categories list ['Rent', 'Utilities','Internet & Phone','Electricity','Water','Gas','Cleaning','Transportation','Insurance','Taxes','HOA / Community Fees','Subscriptions', 'Miscellaneous'] "
            "Output rules: "
            "- Only return the JSON object, no conversation. "
            "- Do not include explanations, comments, or conversational text. "
            "- If any field is missing from the message, infer it when possible or use null. "
        )

        contents = []
        if image_bytes:
            image_part = {"mime_type": "image/jpeg", "data": image_bytes}
            contents.append(image_part)
        
        contents.append(text if text else "Extract the financial data from the image.")

        logging.info(f"Sending prompt to Gemini with text: '{text}' and an image: {'Yes' if image_bytes else 'No'}")
        
        # Use a multimodal model
        response = client.models.generate_content(
            model="gemini-3-flash-preview",
            contents=text,
            #generation_config=types.GenerationConfig(
            #    response_mime_type="application/json"
            #)
            config=types.GenerateContentConfig( # Ahora 'types' ya está definido
                system_instruction=system_instruction,
                response_mime_type="application/json"
            ),
        )
        return response.text
    except Exception as e:
        logging.error(f"An error occurred while communicating with Gemini: {e}")
        return None
