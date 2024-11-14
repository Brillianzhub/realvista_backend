import firebase_admin
from firebase_admin import credentials, messaging

# cred = credentials.Certificate('path/to/serviceAccountKey.json')
# firebase_admin.initialize_app(cred)


def send_push_notification(token, message):
    # See documentation on defining a message payload.
    message = messaging.Message(
        notification=messaging.Notification(
            title='New Update Available!',
            body=message,
        ),
        token=token,
    )

    # Send a message to the device corresponding to the provided
    # registration token.
    response = messaging.send(message)
    # Response is a message ID string.
    print('Successfully sent message:', response)
