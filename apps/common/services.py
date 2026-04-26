import logging
import os

logger = logging.getLogger(__name__)


def send_whatsapp_message(phone_number: str, message: str) -> None:
    """
    WhatsApp integration hook.
    Replace this with your provider integration (Twilio/MSG91/Meta API).
    """
    provider = os.getenv("WHATSAPP_PROVIDER", "console")
    if provider == "console":
        logger.info("WhatsApp -> %s | %s", phone_number, message)
        return

    # Future provider implementations can be added here.
    logger.info("WhatsApp provider '%s' not implemented yet. Message queued in logs.", provider)
