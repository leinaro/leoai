"""Main entry point for the Flask application."""

import logging
import os
from flask import Flask
from dotenv import load_dotenv

from routes import webhook_blueprint

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

# Register the webhook blueprint
app.register_blueprint(webhook_blueprint)

if __name__ == "__main__":
    app.run(debug=True, port=os.getenv("PORT", 8080))
