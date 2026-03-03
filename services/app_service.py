
import logging
from typing import Optional, Tuple

from . import ai_service
from . import google_service
from . import whatsapp_service


from utils.errors import UnAuthorizedUserException
from utils.errors import AIProccesingException

def proccess_whatsapp_message_with_ai(data: dict):
    """Main handler for incoming WhatsApp messages."""
    message_type = message_data.get('type')


def handle_text_message(message_data: dict):
    """Text handler for incoming WhatsApp messages."""
    try:
        logging.debug("text message received")
        message_text = message_data['text']['body']
        return ai_service.process_with_gemini(text=message_text)
    except Exception as e:
        logging.error(f"An error occurred while processing the message: {e}")
        raise AIProccesingException(message=message_text)

def handle_message_with_attachement(message_data: dict, message_type: str):
    """Image handler for incoming WhatsApp messages."""
    try:
        logging.info("image message received")

        # Extraemos la info dinámicamente según sea imagen o documento
        media_info = message_data[message_type] 
        media_id = media_info['id']
        mimetype = media_info['mime_type'] # <--- VITAL: capturamos el tipo real
        caption = media_info.get('caption', '')
        logging.info(f"Received {message_type} ({mimetype}) with caption: '{caption}'")

        return process_media_message(media_id, caption, timestamp, message_type)

    except Exception as e:
        ogging.error(f"An error occurred while processing the message: {e}")
        raise AIProccesingException(message=message_text)



def handle_document_message(data: dict):
    """Document handler for incoming WhatsApp messages."""


def process_media_message(
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
        text=caption, 
        file_bytes=file_bytes
    )
        
    return ai_response, file_bytes

def validate_allowed_users(sender_phone: str) -> None:
    """
    Valida si el número de teléfono está autorizado para usar el servicio.

    Args:
        sender_phone (str): Número de teléfono del usuario que envía el mensaje.

    Raises:
        UnAuthorizedUserException: Si el usuario no está en la lista de autorizados.
    """
    allowed_users = google_service.get_authorized_users()

    if sender_phone not in allowed_users:
        logging.warning(
            f"Usuario {sender_phone} bloqueado. No está en la lista de Usuarios autorizados."
        )
        raise UnAuthorizedUserException(sender_phone)
