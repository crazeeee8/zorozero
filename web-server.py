from flask import Flask
from .config import settings
from .state import STATE

app = Flask(__name__)

@app.route("/")
def home():
    """Provides a simple status page."""
    return f"✅ Bot is alive. Monitoring {settings.SYMBOL}", 200

@app.route("/health")
def health():
    """Health check endpoint for Render."""
    return "ok", 200

def run_flask():
    """Runs the Flask application."""
    # Use a production-ready WSGI server like Gunicorn in your Render start command
    # This is fine for Render's purpose of keeping the service alive
    app.run(host="0.0.0.0", port=settings.PORT, debug=False, use_reloader=False)