"""Handles the main business logic by orchestrating calls to various services."""

import logging
import json
from datetime import datetime
from typing import Optional, Tuple

# Import service modules
from . import ai_service
from . import google_service
from . import whatsapp_service

# Initialize the AI client once
client = ai_service.initialize_gemini()

def handle_whatsapp_message(data: dict):
    """Main handler for incoming WhatsApp messages."""
    try:
        message_data = data['entry'][0]['changes'][0]['value']['messages'][0]
        sender_phone = message_data['from']
        
        allowed_users = google_service.get_authorized_users()
        if sender_phone not in allowed_users:
            logging.warning(f"Usuario {sender_phone} bloqueado. No está en la lista de Sheets {allowed_users}.")
            whatsapp_service.send_whatsapp_message(sender_phone, "Lo siento, no eres un usuario autorizado para usar este chat.")

            return # Meta recibe el OK, pero no hacemos nada

        #whatsapp_service.send_whatsapp_message(sender_phone, "✅ Mensaje recibido. Procesando tus gastos...")

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        message_type = message_data.get('type')

        file_bytes = None
        mimetype = None
        ai_response = None

        if message_type == 'text':
            logging.info("text message received")
            message_text = message_data['text']['body']
            logging.info(f"Received text message: '{message_text}' from {sender_phone}")
            ai_response = ai_service.process_with_gemini(client, message_text)

        elif message_type in ['image', 'document']:
            logging.info("image message received")

            # Extraemos la info dinámicamente según sea imagen o documento
            media_info = message_data[message_type] 
            media_id = media_info['id']
            mimetype = media_info['mime_type'] # <--- VITAL: capturamos el tipo real
            caption = media_info.get('caption', '')
            logging.info(f"Received {message_type} ({mimetype}) with caption: '{caption}' from {sender_phone}")

            ai_response, file_bytes = process_media_message(sender_phone, media_id, caption, timestamp, message_type, historial)
        
        else:
            logging.warning(f"Unsupported message type: {message_type}")

        handle_ai_response(timestamp, sender_phone, ai_response, file_bytes, mimetype)

    except (KeyError, IndexError) as e:
        logging.error(f"Could not parse WhatsApp webhook payload: {e}")
        logging.error(f"Received data: {data}")
        whatsapp_service.send_whatsapp_message(sender_phone, "❌ Could not parse WhatsApp webhook payload.")

def process_media_message(
    sender_phone: str, 
    media_id: str, 
    caption: str, 
    timestamp: str, 
    message_type: str # 'image' o 'document'
) -> Tuple[Optional[str], Optional[bytes]]:
    """
    Procesa un archivo (imagen o PDF) coordinando la descarga de WhatsApp 
    y el análisis de Gemini.
    """
    # 1. Obtener la URL del archivo (WhatsApp usa la misma lógica para ambos)
    media_url = whatsapp_service.get_media_url(media_id)
    if not media_url:
        # Consider sending a WhatsApp message back to the user
        logging.error(f"No se pudo obtener la URL para el {message_type}")
        return None, None

    # 2. Descargar los bytes (valido para jpg, png, pdf, etc.)
    file_bytes = whatsapp_service.download_media_content(media_url)
    if not file_bytes:
        # Consider sending a WhatsApp message back to the user
        logging.error(f"No se pudieron descargar los bytes del {message_type}")
        return None, None
    
    # 3. Mandar a Gemini
    # Gemini 1.5 detecta automáticamente si los bytes son imagen o PDF
    logging.info(f"Enviando {message_type} a Gemini para análisis...")
    ai_response = ai_service.process_with_gemini(
        client, 
        text=caption, 
        file_bytes=file_bytes
    )
        
    return ai_response, file_bytes

def handle_ai_response(
    timestamp: str, 
    sender_phone: str, 
    ai_response: Optional[str], 
    file_bytes: Optional[bytes] = None,
    mimetype: Optional[str] = None
):
    """Handles the response from the AI service, saving data and images."""
    if not ai_response:
        logging.warning("AI response was empty. Cannot process further.")
        whatsapp_service.send_whatsapp_message(sender_phone, "❌ AI response was empty. Cannot process further.")
        return

    try:
        logging.info(f"AI response: {ai_response}")
        print(f"AI response: {ai_response}")

        expense_data = json.loads(ai_response)

        logging.info("expense_data")

        valid_expense = expense_data.get('valid_expense') or False
        if not valid_expense:
            logging.warning("Invalid expense. Not saving to Google Sheets.")
            error_message = expense_data.get('message') or "❌ Invalid expense. Not saving to Google Sheets."

            whatsapp_service.send_whatsapp_message(sender_number, error_message)

        date_for_drive = expense_data.get('date') or timestamp
        folder = expense_data.get('folder', 'Unknown')
        concept = expense_data.get('concept', '')
    
        link_drive = ""

            
        if file_bytes and mimetype:
            ext = ".pdf" if "pdf" in mimetype else ".jpg"
            
            clean_concept = str(concept).replace(" ", "_")[:20] # Limitamos largo
            file_name = f"{folder}_{clean_concept}_{str(timestamp).replace(' ', '_').replace(':', '-')}{ext}"

            link_drive = google_service.save_file(file_bytes, date_for_drive, file_name, mimetype)

        # Prepare the row for Google Sheets
        # Date	Concept	Amount	Currency	Category	Subcategory	Sender	Timestamp
        
        row_to_add = [
            date_for_drive,         # C: Fecha de la factura (extraída por IA)
            concept,                # D: Concepto
            expense_data.get('amount', ''),
            expense_data.get('currency', ''),
            expense_data.get('category', ''),
            expense_data.get('subcategory', ''),
            sender_phone,           # B: Quién lo envió
            timestamp,              # A: Cuándo se envió el mensaje
            link_drive              # I: Link directo al archivo
        ]
        logging.info(f"row_to_add {row_to_add}")

        
        google_service.add_row_to_sheet(row_to_add)
        
        # Optionally, send a success message via WhatsApp
        # whatsapp_service.send_whatsapp_message(to=sender_phone, message="Data processed successfully.")
        logging.info(f"✅ Transacción registrada: {concept} - {folder}")
        print(f"✅ Transacción registrada: {concept} - {folder}")

        mensaje = (
                f"Se creó exitosamente una entrada con concepto '{concept}', "
                f"valor {expense_data.get('amount', '')} {expense_data.get('currency', '')}, "
                f"categoría '{expense_data.get('category', '')}', "
                f"subcategoría '{expense_data.get('subcategory', '')}'. "
                )

        whatsapp_service.send_whatsapp_message(sender_phone, "📝 ¡Listo! Datos agregados correctamente a tu Google Sheet.")

    except json.JSONDecodeError:
        logging.error(f"Could not parse AI response as JSON: {ai_response}")
        whatsapp_service.send_whatsapp_message(sender_phone, "❌ Could not parse AI response as JSON")
    except Exception as e:
        logging.error(f"An error occurred during data preparation: {e}")
        whatsapp_service.send_whatsapp_message(sender_phone, "❌ An error occurred during data preparation:")