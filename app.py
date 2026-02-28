"""Main entry point for the Flask application."""

import logging
import os
from flask import Flask, render_template
from dotenv import load_dotenv

from routes import webhook_blueprint

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

# Register the webhook blueprint for API endpoints
app.register_blueprint(webhook_blueprint, url_prefix='/api')

# --- Add Privacy Policy Route ---
@app.route('/privacy', methods=['GET'])
def privacy_policy():
    """Renders the privacy policy page."""
    # Flask will automatically look for this file in the 'templates' folder
    return render_template('privacy_policy.html')

@app.route('/', methods=['GET'])
def home():
    """Optional: A simple homepage to show the service is running."""
    return "<h1>Leo AI Assistant Service is running.</h1><p>Visit <a href='/privacy'>/privacy</a> for our privacy policy.</p>", 200

if __name__ == "__main__":
    # Use Gunicorn's port if available, otherwise default to 8080
    port = int(os.environ.get("PORT", 8080))
    app.run(debug=False, host='0.0.0.0', port=port)
