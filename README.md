# WhatsApp, Gemini, and Google Sheets Integration

This Flask application acts as a webhook to integrate WhatsApp, Google Gemini AI, Google Sheets, and Google Drive.

## Features

- **Webhook Verification:** Verifies the webhook with WhatsApp.
- **Text Processing:** Parses incoming text messages using Gemini to extract structured data (Concept, Amount, Category) and appends it to a Google Sheet.
- **Image Processing:** Downloads incoming images, uploads them to a specified Google Drive folder, and logs the Drive URL in the Google Sheet.
- **Secure:** Validates incoming requests from WhatsApp using the X-Hub-Signature-256 header.
- **Modular:** The project is structured with Blueprints and services for better organization and scalability.

## Project Structure

```
.
├── app.py
├── routes.py
├── services
│   ├── ai_service.py
│   ├── google_service.py
│   └── whatsapp_service.py
├── utils
│   └── security.py
├── requirements.txt
├── .env.example
└── README.md
```

## Setup

1.  **Clone the repository:**

    ```bash
    git clone <repository-url>
    cd <repository-directory>
    ```

2.  **Create a virtual environment and install dependencies:**

    ```bash
    python3 -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt
    ```

3.  **Set up environment variables:**

    -   Rename `.env.example` to `.env`.
    -   Fill in the required values for your WhatsApp, Gemini, and Google credentials.

4.  **Set up Google Service Account:**

    -   Follow the instructions in the [Google Cloud documentation](https://cloud.google.com/iam/docs/creating-managing-service-account-keys) to create a service account and download the JSON key file.
    -   Save the JSON key file as `service_account.json` in the root directory of the project.
    -   Enable the Google Drive API and Google Sheets API for your project in the Google Cloud Console.
    -   Share your Google Sheet and Google Drive folder with the service account's email address.

## Running the Application

```bash
source .venv/bin/activate
flask run
```

## Disclaimer

This project is intended for educational purposes and should not be used in a production environment without further security hardening and testing.
