import json
import logging

from django.conf import settings

logger = logging.getLogger(__name__)

_firebase_app = None


def _load_firebase_certificate():
    from firebase_admin import credentials

    raw = getattr(settings, 'FIREBASE_CREDENTIALS_JSON', '') or ''
    if raw.strip():
        return credentials.Certificate(json.loads(raw))

    cred_path = getattr(settings, 'FIREBASE_CREDENTIALS_PATH', '') or ''
    if cred_path:
        return credentials.Certificate(cred_path)
    return None


def _get_firebase_app():
    global _firebase_app
    if _firebase_app is not None:
        return _firebase_app
    try:
        import firebase_admin
        if firebase_admin._apps:
            _firebase_app = firebase_admin.get_app()
            return _firebase_app
        cert = _load_firebase_certificate()
        if cert is None:
            return None
        _firebase_app = firebase_admin.initialize_app(cert)
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
            android=messaging.AndroidConfig(
                priority='high',
                notification=messaging.AndroidNotification(
                    channel_id='quikgarage_channel',
                ),
            ),
            apns=messaging.APNSConfig(
                headers={'apns-priority': '10'},
                payload=messaging.APNSPayload(
                    aps=messaging.Aps(sound='default', badge=1),
                ),
            ),
        )
        messaging.send(message)
        return True
    except Exception as exc:
        logger.error('FCM send failed: %s', exc)
        return False
