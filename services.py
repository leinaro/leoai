"""Handles business logic for the application, such as interacting with external APIs."""

import os
import logging
import requests
import json
import gspread
from datetime import datetime
from google.oauth2.service_account import Credentials
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

# --- Google Sheets Service ---
def add_row_to_sheet(data_row: list):
    """Appends a new row to the configured Google Sheet."""
    sheet_id = os.getenv("GOOGLE_SHEET_ID")
    creds_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    
    if not sheet_id or not creds_path:
        logging.error("Google Sheet ID or Credentials Path not found in environment variables.")
        return

    try:
        scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_file(creds_path, scopes=scopes)
        gs_client = gspread.authorize(creds)
        
        sheet = gs_client.open_by_key(sheet_id).sheet1
        sheet.append_row(data_row)
        logging.info(f"Successfully added row to Google Sheet: {data_row}")
    except FileNotFoundError:
        logging.error(f"Credentials file not found at path: {creds_path}. Make sure the file exists.")
    except Exception as e:
        logging.error(f"An error occurred while writing to Google Sheets: {e}")

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
            "Act as a Senior Financial Assistant. From each user message, extract financial transaction data and return it as a JSON object with the following fields: "
            "{'concept': string, 'amount': number, 'category': string, 'currency': string, 'date': string, 'folder': string} "
            "Folder rules: "
            "- The 'folder' field MUST be one of the following values: ['Salitre', 'Tramonte', 'Villa', 'Manuela Sancho']. "
            "- Infer the folder based on contextual clues such as location, property name, people involved, or recurring patterns. "
            "- If the folder cannot be confidently determined, set 'folder' to 'Unknown'. "
            "Category rules: "
            "- Assign the most appropriate category based on the nature of the expense or income. "
            "- Use only predefined categories list ['Rent', 'Utilities','Internet & Phone','Electricity','Water','Gas','Cleaning','Transportation','Insurance','Taxes','HOA / Community Fees','Subscriptions', 'Miscellaneous'] "
            "Output rules: "
            "- Only return the JSON object, no conversation. "
            "- Do not include explanations, comments, or conversational text. "
            "- If any field is missing from the message, infer it when possible or use null. "
        )

        response = client.models.generate_content(
            model="gemini-3-flash-preview",
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                response_mime_type="application/json" # Fuerza la salida en JSON
            ),
            contents=text
        )
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
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        logging.info(f"Received message: '{message_text}' from {sender_phone}")

        # Process the message with Gemini
        ai_response = process_with_gemini(message_text)

        if ai_response:
            # --- GOOGLE SHEETS LOGIC ---
            try:
                # The AI returns a JSON string, parse it into a Python dict
                expense_data = json.loads(ai_response)
                
                # Prepare the row for Google Sheets in the correct order
                row_to_add = [
                    timestamp,
                    sender_phone,
                    expense_data.get('date', ''),
                    expense_data.get('concept', ''),
                    expense_data.get('amount', ''),
                    expense_data.get('category', ''),
                    expense_data.get('currency', ''),
                    expense_data.get('folder', '')
                ]
                
                # Add the data to the sheet
                add_row_to_sheet(row_to_add)
                
            except json.JSONDecodeError:
                logging.error(f"Could not parse AI response as JSON: {ai_response}")
            except Exception as e:
                logging.error(f"An error occurred during Google Sheets data preparation: {e}")
            # --- END GOOGLE SHEETS LOGIC ---

            print(f"ai response {ai_response}")
            send_whatsapp_message(to=sender_phone, message=ai_response)
        else:
            # Send a fallback message if AI processing fails
            logging.warning("AI response was empty. Sending fallback message.")
            send_whatsapp_message(to=sender_phone, message="Sorry, I couldn't process your request.")

    except (KeyError, IndexError) as e:
        logging.error(f"Could not parse WhatsApp webhook payload: {e}")
        logging.error(f"Received data: {data}")
