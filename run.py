import asyncio
import threading
import logging
from bot.core import monitor
from bot.web_server import run_flask
from bot.config import settings

def main():
    """
    Initializes and runs the bot and the keep-alive web server.
    """
    # Configure logging
    log_format = '%(asctime)s - %(levelname)s - %(message)s'
    logging.basicConfig(level=logging.INFO, format=log_format)

    # Start the Flask keep-alive server in a separate thread
    # This is required for deployment on platforms like Render.
    logging.info(f"Starting keep-alive web server on port {settings.PORT}...")
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()

    # Start the main asynchronous bot logic
    logging.info("Starting bot monitoring loop...")
    try:
        asyncio.run(monitor())
    except KeyboardInterrupt:
        logging.info("Bot shutting down manually.")
    except Exception as e:
        logging.error(f"A critical error occurred in the main loop: {e}", exc_info=True)

if __name__ == "__main__":
    main()