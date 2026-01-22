"""Handles the webhook routes for the Flask application."""

import logging
import os
from flask import Blueprint, request, jsonify

from services import ai_service, google_service, whatsapp_service
from utils.security import validate_whatsapp_signature

webhook_blueprint = Blueprint("webhook", __name__)

@webhook_blueprint.route("/webhook", methods=["GET", "POST"])
def webhook():
    """Handles Webhook verification and incoming events."""
    if request.method == "GET":
        # Webhook verification
        verify_token = os.getenv("VERIFY_TOKEN")
        mode = request.args.get("hub.mode")
        token = request.args.get("hub.verify_token")
        challenge = request.args.get("hub.challenge")

        if mode == "subscribe" and token == verify_token:
            logging.info("Webhook verified")
            return challenge, 200
        else:
            logging.error("Webhook verification failed")
            return "Forbidden", 403

    elif request.method == "POST":
        # Handle incoming events
        signature = request.headers.get("X-Hub-Signature-256")
        if not validate_whatsapp_signature(
            request.data, signature, os.getenv("WHATSAPP_APP_SECRET")
        ):
            logging.warning("Invalid signature")
            return "Forbidden", 403

        data = request.get_json()
        if "entry" not in data:
            return jsonify({"status": "error", "message": "Invalid payload"}), 400
        
        for entry in data.get("entry", []):
            for change in entry.get("changes", []):
                value = change.get("value", {})
                if "messages" in value:
                    for message in value.get("messages", []):
                        handle_message(message)

        return jsonify({"status": "ok"}), 200

def handle_message(message: dict):
    """Handles incoming messages from WhatsApp.

    Args:
        message: A dictionary representing the message object from WhatsApp.
    """
    from_number = message.get("from")
    msg_type = message.get("type")

    if msg_type == "text":
        text = message["text"]["body"]
        ai_response = ai_service.get_gemini_response(text)
        if ai_response:
            google_service.append_to_sheet(ai_response)
            whatsapp_service.send_whatsapp_message(from_number, "Data logged successfully.")
        else:
            whatsapp_service.send_whatsapp_message(from_number, "Sorry, I couldn't process that.")

    elif msg_type == "image":
        image_id = message["image"]["id"]
        media_url = whatsapp_service.get_media_url(image_id)
        if media_url:
            media_content = whatsapp_service.download_media(media_url)
            if media_content:
                drive_url = google_service.upload_to_drive(media_content, f"{image_id}.jpg")
                if drive_url:
                    google_service.log_drive_url(drive_url)
                    whatsapp_service.send_whatsapp_message(from_number, f"Image uploaded: {drive_url}")
                else:
                    whatsapp_service.send_whatsapp_message(from_number, "Failed to upload image.")
            else:
                whatsapp_service.send_whatsapp_message(from_number, "Failed to download image.")
        else:
            whatsapp_service.send_whatsapp_message(from_number, "Failed to get image URL.")
