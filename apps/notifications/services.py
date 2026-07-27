import json
import logging

from django.conf import settings

logger = logging.getLogger(__name__)

_firebase_app = None


def _get_firebase_app():
    global _firebase_app
    if _firebase_app is not None:
        return _firebase_app
    cred_path = settings.FIREBASE_CREDENTIALS_PATH
    if not cred_path:
        return None
    try:
        import firebase_admin
        from firebase_admin import credentials
        if not firebase_admin._apps:
            cred = credentials.Certificate(cred_path)
            _firebase_app = firebase_admin.initialize_app(cred)
        else:
            _firebase_app = firebase_admin.get_app()
    except Exception as exc:
        logger.error('Firebase init failed: %s', exc)
        return None
    return _firebase_app


def send_fcm_to_token(token: str, title: str, body: str, data: dict | None = None):
    app = _get_firebase_app()
    if not app:
        logger.info('FCM skipped (no Firebase credentials): %s', title)
        return False
    try:
        from firebase_admin import messaging
        message = messaging.Message(
            notification=messaging.Notification(title=title, body=body),
            data={k: str(v) for k, v in (data or {}).items()},
            token=token,
        )
        messaging.send(message)
        return True
    except Exception as exc:
        logger.error('FCM send failed: %s', exc)
        return False
