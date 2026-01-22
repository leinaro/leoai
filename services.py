"""Handles business logic for the application, such as interacting with external APIs."""

import os
import logging
import requests
#import google.genai as genai
from google import genai
from google.genai import types

from typing import Optional

# --- Gemini AI Model Initialization ---

def initialize_gemini():
    """Initializes and returns the Gemini generative model.
    
    Returns:
        A configured GenerativeModel instance or None if initialization fails.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    
    if not api_key:
        logging.error("GEMINI_API_KEY not found in environment variables. The model cannot be initialized.")
        return None

    logging.info("GEMINI_API_KEY found. Configuring Gemini...")
    
    try:
        client = genai.Client(api_key=api_key)
        #genai.configure(api_key=api_key)
        
        #model = genai.GenerativeModel('gemini-3-flash-preview')
        logging.info("Gemini model initialized successfully.")
        return client
    except Exception as e:
        # Log the specific exception from the Google AI library
        logging.error(f"An error occurred during Gemini model initialization: {e}")
        logging.error("This might be due to an invalid API key or other configuration issues.")
        return None

# Initialize the model when the service module is loaded
client = initialize_gemini()

# --- WhatsApp Business API Functions ---

def send_whatsapp_message(to: str, message: str):
    """Sends a WhatsApp message using the Meta Graph API."""
    access_token = os.getenv("WHATSAPP_ACCESS_TOKEN")
    phone_number_id = os.getenv("WHATSAPP_PHONE_NUMBER_ID")
    
    if not all([access_token, phone_number_id]):
        logging.error("WhatsApp API credentials not found in environment variables.")
        return

    url = f"https://graph.facebook.com/v19.0/{phone_number_id}/messages"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }
    data = {
        "messaging_product": "whatsapp",
        "to": to,
        "text": {"body": message}
    }
    
    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status() # Raises an HTTPError for bad responses (4xx or 5xx)
        logging.info(f"WhatsApp message sent to {to}. Status: {response.status_code}")
    except requests.exceptions.RequestException as e:
        logging.error(f"Error sending WhatsApp message: {e}")

# --- Main Service Logic ---

def process_with_gemini(text: str) -> Optional[str]:
    """Processes the given text using the Gemini model."""
    if not client:
        # This log will now only appear if initialization failed earlier
        logging.error("Cannot process text because the Gemini model is not available.")
        return None
    
    try:
        logging.info(f"Sending prompt to Gemini: '{text}'")
        #response = model.generate_content(text)
        # Instrucciones del sistema (Accountant Assistant)
        system_instruction = (
            "Act as a Senior Financial Assistant. Extract data from messages into JSON: "
            "{'concept': string, 'amount': number, 'category': string, 'currency': string}. "
            "Only return the JSON object, no conversation."
        )

        response = client.models.generate_content(
            model="gemini-3-flash-preview",
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                response_mime_type="application/json" # Fuerza la salida en JSON
            ),
            contents=text
        )
        print(response.text)
        return response.text
    except Exception as e:
        logging.error(f"An error occurred while communicating with Gemini: {e}")
        return None

def handle_whatsapp_message(data: dict):
    """Main handler for incoming WhatsApp messages."""
    # Extract relevant information from the webhook payload
    # (This is a simplified extraction)
    try:
        message_data = data['entry'][0]['changes'][0]['value']['messages'][0]
        sender_phone = message_data['from']
        message_text = message_data['text']['body']
        logging.info(f"Received message: '{message_text}' from {sender_phone}")

        # Process the message with Gemini
        ai_response = process_with_gemini(message_text)

        if ai_response:
            # Send the AI's response back to the user via WhatsApp
            print(f"ai response {ai_response}")
            #send_whatsapp_message(to=sender_phone, message=ai_response)
        else:
            # Send a fallback message if AI processing fails
            logging.warning("AI response was empty. Sending fallback message.")
            #send_whatsapp_message(to=sender_phone, message="Sorry, I couldn't process your request.")

    except (KeyError, IndexError) as e:
        logging.error(f"Could not parse WhatsApp webhook payload: {e}")
        logging.error(f"Received data: {data}")
