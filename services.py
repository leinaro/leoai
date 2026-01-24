"""Handles business logic for the application, such as interacting with external APIs."""

import os
import logging
import requests
import json
import gspread
from datetime import datetime
from google.oauth2.service_account import Credentials
from google import genai
from google.genai import types

from typing import Optional, Tuple


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
        logging.info("Gemini client initialized successfully.")
        return client
    except Exception as e:
        # Log the specific exception from the Google AI library
        logging.error(f"An error occurred during Gemini model initialization: {e}")
        logging.error("This might be due to an invalid API key or other configuration issues.")
        return None

# Initialize the client when the service module is loaded
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

def get_image_url(image_id: str) -> Optional[str]:
    """Retrieves the media URL of an image from the WhatsApp API."""
    access_token = os.getenv("WHATSAPP_ACCESS_TOKEN")
    if not access_token:
        logging.error("WHATSAPP_ACCESS_TOKEN not found.")
        return None
    url = f"https://graph.facebook.com/v20.0/{image_id}"
    headers = {"Authorization": f"Bearer {access_token}"}
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        media_data = response.json()
        return media_data.get("url")
    except requests.exceptions.RequestException as e:
        logging.error(f"Error getting image URL: {e}")
        return None

def download_image_content(media_url: str) -> Optional[bytes]:
    """Downloads the content of an image from its media URL."""
    access_token = os.getenv("WHATSAPP_ACCESS_TOKEN")
    if not access_token:
        logging.error("WHATSAPP_ACCESS_TOKEN not found.")
        return None
    headers = {"Authorization": f"Bearer {access_token}"}
    try:
        response = requests.get(media_url, headers=headers)
        response.raise_for_status()
        return response.content
    except requests.exceptions.RequestException as e:
        logging.error(f"Error downloading image content: {e}")
        return None

def save_image(image_bytes: bytes, folder_name: str, file_name: str) -> Optional[str]:
    """Saves image bytes to a specified local folder."""
    try:
        folder_id = os.getenv("GOOGLE_DRIVE_FOLDER_ID")
        subfolder_id = get_or_create_subfolder(folder_name, folder_id)
        link_drive = upload_image_to_drive(imagen_bytes, file_name, subfolder_id)
        logging.info(f"Image saved to {file_path}")
        return link_drive
    except Exception as e:
        logging.error(f"Error saving image: {e}")
        return None

def get_or_create_subfolder(folder_name: str, parent_id: str):
    """Busca una subcarpeta por nombre dentro de una carpeta padre. Si no existe, la crea."""
    creds_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    
    try:
        scopes = ["https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_file(creds_path, scopes=scopes)
        service = build('drive', 'v3', credentials=creds)

        # 1. Intentar buscar la carpeta
        query = (f"name = '{folder_name}' and "
                 f"'{parent_id}' in parents and "
                 f"mimeType = 'application/vnd.google-apps.folder' and "
                 f"trashed = false")
        
        results = service.files().list(q=query, fields="files(id)").execute()
        items = results.get('files', [])

        if items:
            logging.info(f"Subcarpeta encontrada: {folder_name} (ID: {items[0]['id']})")
            return items[0]['id']

        # 2. Si no existe, crearla
        folder_metadata = {
            'name': folder_name,
            'parents': [parent_id],
            'mimeType': 'application/vnd.google-apps.folder'
        }
        
        new_folder = service.files().create(body=folder_metadata, fields='id').execute()
        logging.info(f"Nueva subcarpeta creada: {folder_name} (ID: {new_folder['id']})")
        return new_folder.get('id')

    except Exception as e:
        logging.error(f"Error al gestionar la subcarpeta en Drive: {e}")
        return parent_id  # Si falla, devolvemos el ID padre para no romper el flujo

def upload_image_to_drive(image_bytes: bytes, filename: str, folder_id: str):
    """Subes bytes de imagen a una carpeta de Drive y devuelve el link público."""
    creds_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    
    try:
        scopes = ["https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_file(creds_path, scopes=scopes)
        
        # Construimos el servicio de Drive
        service = build('drive', 'v3', credentials=creds)

        file_metadata = {
            'name': filename,
            'parents': [folder_id]
        }
        
        # Convertimos los bytes en un objeto que Google puede leer
        media = MediaIoBaseUpload(io.BytesIO(image_bytes), mimetype='image/jpeg', resumable=True)

        # 1. Crear el archivo
        file = service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id, webViewLink'
        ).execute()

        # 2. Hacerlo público para que el link funcione en el Sheet (Opcional)
        service.permissions().create(
            fileId=file.get('id'),
            body={'type': 'anyone', 'role': 'viewer'}
        ).execute()

        logging.info(f"Archivo subido a Drive: {file.get('id')}")
        return file.get('webViewLink')

    except Exception as e:
        logging.error(f"Error subiendo a Google Drive: {e}")
        return None

# --- Main Service Logic ---

def process_with_gemini(text: str, image_bytes: Optional[bytes] = None) -> Optional[str]:
    """Processes the given text and/or image using the Gemini model."""
    if not client:
        # This log will now only appear if initialization failed earlier
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
        
        # Add text prompt, which is required. If no text, add a default prompt.
        contents.append(text if text else "Extract the financial data from the image.")

        logging.info(f"Sending prompt to Gemini with text: '{text}' and an image: {'Yes' if image_bytes else 'No'}")
        
        # Use a multimodal model
        response = client.models.generate_content(
            model="gemini-3-flash-preview",
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                response_mime_type="application/json" # Fuerza la salida en JSON
            ),
            contents=contents,
        )
        return response.text
    except Exception as e:
        logging.error(f"An error occurred while communicating with Gemini: {e}")
        return None

def handle_ai_response(timestamp: str, sender_phone: str, ai_response: Optional[str], image_bytes: Optional[bytes] = None): 
    """Main handler for incoming AI response."""
    if ai_response:
        # --- GOOGLE SHEETS LOGIC ---
        try:
            # The AI returns a JSON string, parse it into a Python dict
            expense_data = json.loads(ai_response)
            folder = expense_data.get('folder', 'Unknown')
            concept = expense_data.get('concept', ''),

            link_drive = ""
            if image_bytes:
                logging.info(f"image bytes: {image_bytes}")
                file_name = f"{image_id}.jpg"
                link_drive = save_image(image_bytes, folder, file_name)

            # Prepare the row for Google Sheets in the correct order
            row_to_add = [
                timestamp,
                sender_phone,
                expense_data.get('date', ''),
                expense_data.get('concept', ''),
                expense_data.get('amount', ''),
                expense_data.get('category', ''),
                expense_data.get('currency', ''),
                folder,
                link_drive
            ]
            
            # Add the data to the sheet
            add_row_to_sheet(row_to_add)
            
        except json.JSONDecodeError:
            logging.error(f"Could not parse AI response as JSON: {ai_response}")
        except Exception as e:
            logging.error(f"An error occurred during Google Sheets data preparation: {e}")
        # --- END GOOGLE SHEETS LOGIC ---

        print(f"ai response {ai_response}")
        #send_whatsapp_message(to=sender_phone, message=ai_response)
        #send_whatsapp_message(to=sender_phone, message=f"Image processed and data saved to folder '{folder}'.")

    else:
        # Send a fallback message if AI processing fails
        logging.warning("AI response was empty. Sending fallback message.")
        #send_whatsapp_message(to=sender_phone, message="Sorry, I couldn't process your request.")
        # Fallback if AI fails: save image to 'Unknown' and notify user
        #file_name = f"{image_id}.jpg"
        #save_image(image_bytes, folder, file_name)
        #send_whatsapp_message(to=sender_phone, message=f"I couldn't understand the data, but I've saved the image to the '{folder}' folder.")


def handle_whatsapp_message(data: dict):
    """Main handler for incoming WhatsApp messages."""
    # Extract relevant information from the webhook payload
    # (This is a simplified extraction)
    try:
        message_data = data['entry'][0]['changes'][0]['value']['messages'][0]
        sender_phone = message_data['from']
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        message_type = message_data.get('type')

        image_bytes = None
        if message_type == 'text':
            message_text = message_data['text']['body']
            logging.info(f"Received text message: '{message_text}' from {sender_phone}")
            ai_response = process_with_gemini(message_text)
        elif message_type == 'image':
            image_id = message_data['image']['id']
            caption = message_data['image'].get('caption', '')
            logging.info(f"Received image with caption: '{caption}' from {sender_phone}")
            ai_response, image_bytes = process_image_message(sender_phone, image_id, caption, timestamp)
        else:
            logging.warning(f"Unsupported message type: {message_type}")

        handle_ai_response(timestamp, sender_phone, ai_response, image_bytes)
    except (KeyError, IndexError) as e:
        logging.error(f"Could not parse WhatsApp webhook payload: {e}")
        logging.error(f"Received data: {data}")

    
def process_image_message(sender_phone: str, image_id: str, caption: str, timestamp: str) -> Tuple[Optional[str], Optional[bytes]]:
    """Processes an image message with an optional caption."""
    media_url = get_image_url(image_id)
    if not media_url:
        #send_whatsapp_message(to=sender_phone, message="Sorry, I could not retrieve the image URL.")
        return

    image_bytes = download_image_content(media_url)
    if not image_bytes:
        #send_whatsapp_message(to=sender_phone, message="Sorry, I failed to download the image.")
        return
        
    return process_with_gemini(text=caption, image_bytes=image_bytes), image_bytes