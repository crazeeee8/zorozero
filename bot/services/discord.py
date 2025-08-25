import logging
import aiohttp
from ..config import settings
from ..state import STATE
from ..utils import async_backoff

async def _ensure_session() -> aiohttp.ClientSession:
    """Ensures a shared aiohttp session is available."""
    if STATE.session and not STATE.session.closed:
        return STATE.session
    timeout = aiohttp.ClientTimeout(total=30, connect=10, sock_read=20)
    STATE.session = aiohttp.ClientSession(timeout=timeout)
    return STATE.session

async def send_message(content: str):
    """Sends a simple text message to the Discord webhook."""
    if not settings.DISCORD_WEBHOOK:
        logging.warning("Discord webhook not configured. Cannot send message.")
        return

    session = await _ensure_session()

    async def _post():
        async with session.post(settings.DISCORD_WEBHOOK, json={"content": content}) as resp:
            resp.raise_for_status()

    try:
        await async_backoff(_post, label="discord.send_message")
    except Exception as e:
        logging.error(f"Discord message failed: {e}")

async def send_file(content: str, file_bytes: bytes, filename: str):
    """Sends a message with an image file to the Discord webhook."""
    if not settings.DISCORD_WEBHOOK:
        logging.warning("Discord webhook not configured. Cannot send file.")
        return

    session = await _ensure_session()
    
    async def _post():
        with aiohttp.FormData() as form:
            form.add_field('payload_json', f'{{"content": "{content}"}}')
            form.add_field('file', file_bytes, filename=filename, content_type='image/png')
            
            async with session.post(settings.DISCORD_WEBHOOK, data=form) as resp:
                resp.raise_for_status()

    try:
        await async_backoff(_post, label="discord.send_file")
    except Exception as e:
        logging.error(f"Discord file upload failed: {e}")