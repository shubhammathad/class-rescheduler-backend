"""
Firebase utilities (safe dev mode)

Firebase will only initialize if:
- firebase_admin is installed
- serviceAccountKey.json exists

Otherwise, notifications are silently skipped.
"""

import os

try:
    import firebase_admin
    from firebase_admin import credentials, messaging

    KEY_PATH = "serviceAccountKey.json"

    if not firebase_admin._apps and os.path.exists(KEY_PATH):
        cred = credentials.Certificate(KEY_PATH)
        firebase_admin.initialize_app(cred)

    FIREBASE_ENABLED = firebase_admin._apps

except Exception as e:
    print("Firebase disabled:", e)
    FIREBASE_ENABLED = False


def send_push_notification(tokens, title, body, data=None):
    if not FIREBASE_ENABLED:
        print("Firebase not enabled. Notification skipped.")
        return

    if not tokens:
        return

    message = messaging.MulticastMessage(
        notification=messaging.Notification(
            title=title,
            body=body,
        ),
        data=data or {},
        tokens=tokens,
    )

    try:
        response = messaging.send_multicast(message)
        print(f"Sent {response.success_count} notifications.")
    except Exception as e:
        print("FCM error:", e)
