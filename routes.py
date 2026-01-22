"""Defines the webhook routes for the application."""

import os
import logging
from flask import Blueprint, request, jsonify, Response

# Import the main handler function from the services module
from services import handle_whatsapp_message

# Create a Blueprint for the webhook routes
webhook_blueprint = Blueprint('webhook', __name__)

# Get the verification token from environment variables
VERIFY_TOKEN = os.getenv("VERIFY_TOKEN")

@webhook_blueprint.route('/webhook', methods=['GET', 'POST'])
def webhook():
    """Handles incoming webhook requests from WhatsApp."""
    if request.method == 'GET':
        # This is the verification request from Facebook/Meta
        logging.info("Received webhook verification request.")
        mode = request.args.get('hub.mode')
        token = request.args.get('hub.verify_token')
        challenge = request.args.get('hub.challenge')

        if mode == 'subscribe' and token == VERIFY_TOKEN:
            logging.info("Webhook verified successfully!")
            return Response(challenge, status=200)
        else:
            logging.warning(f"Webhook verification failed. Token mismatch or invalid mode. Token received: {token}")
            return Response("Verification failed", status=403)

    elif request.method == 'POST':
        # This is an incoming message from a user
        data = request.get_json()
        logging.info("Received incoming message payload.")
        
        # Pass the entire payload to the handler function in services
        handle_whatsapp_message(data)
        
        # Return a 200 OK to acknowledge receipt of the message
        return jsonify({"status": "ok"}), 200
