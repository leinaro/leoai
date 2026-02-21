"""Handles all interactions with the Gemini AI model."""

import logging
from typing import Optional, List

from google import genai
from google.genai import types

from .secrets import get_secret # Import our secret helper

# --- Gemini AI Model Initialization ---

def initialize_gemini():
    """Initializes and returns the Gemini client.
    
    Returns:
        A configured Client instance or None if initialization fails.
    """
    api_key = get_secret("GEMINI_API_KEY")

    if not api_key:
        logging.error("GEMINI_API_KEY could not be retrieved from Secret Manager.")
        return None

    logging.info("GEMINI_API_KEY found. Configuring Gemini...")
    
    try:
        client = genai.Client(api_key=api_key)
        logging.info("Gemini client initialized successfully.")
        return client
    except Exception as e:
        logging.error(f"An error occurred during Gemini client initialization: {e}")
        return None

def process_with_gemini(client, text: str, file_bytes: Optional[bytes] = None, mimetype: Optional[str] = None) -> Optional[str]:
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

        parts = []

        if file_bytes and mimetype:
            parts.append(
                types.Part.from_bytes(
                    data=file_bytes,
                    mime_type=mimetype
                )
            )

        #prompt_text = f"Extract the financial data from this document/image/text and merge with information from {text}"
        parts.append(types.Part.from_text(text=text if text else "Analiza este documento."))
        
        logging.info(f"Sending prompt to Gemini with text: '{text}' and an image: {'Yes' if file_bytes else 'No'}")
        
        # Use a multimodal model
        response = client.models.generate_content(
            #model="gemini-3-flash-preview",
            model="gemini-1.5-flash",
            contents=text,
            # todavia no funcionan las imagenes
            #contents=contents, # <--- IMPORTANTE: Aquí pasamos la lista completa
            #contents=[types.Content(role="user", parts=parts)], # <--- Formato robusto

            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                response_mime_type="application/json"
            ),
        )
        logging.info(f"gemini response {response}")

        return response.text
    except Exception as e:
        logging.error(f"An error occurred while communicating with Gemini: {e}")
        return None
