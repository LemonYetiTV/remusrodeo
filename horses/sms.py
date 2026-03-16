import os
from twilio.rest import Client


def send_inquiry_sms(inquiry):

    account_sid = os.environ.get("TWILIO_ACCOUNT_SID")
    auth_token = os.environ.get("TWILIO_AUTH_TOKEN")
    twilio_number = os.environ.get("TWILIO_PHONE_NUMBER")

    owner_phone = os.environ.get("OWNER_ALERT_PHONE")
    trainer_phone = os.environ.get("TRAINER_ALERT_PHONE")

    client = Client(account_sid, auth_token)

    horse = inquiry.horse
    horse_name = horse.barn_name if horse else "Unknown Horse"
    horse_id = horse.program_id if horse else ""

    body = (
        f"🐎 NEW HORSE INQUIRY\n\n"
        f"{horse_id} {horse_name}\n"
        f"From: {inquiry.name}\n"
        f"Phone: {inquiry.phone}\n"
        f"Message: {inquiry.message[:120]}"
    )

    recipients = [owner_phone, trainer_phone]

    for number in recipients:
        if number:
            client.messages.create(
                body=body,
                from_=twilio_number,
                to=number
            )
