from __future__ import annotations

from io import BytesIO
from pathlib import Path
import os

from django.conf import settings
from django.core.files.base import ContentFile
from PIL import Image, ImageDraw, ImageFont
from twilio.rest import Client

from .models import Horse


FLYER_WIDTH = 1200
FLYER_HEIGHT = 630
PHOTO_WIDTH = 720
PANEL_WIDTH = FLYER_WIDTH - PHOTO_WIDTH


def _font(size: int, bold: bool = False):
    candidates = []
    if bold:
        candidates = [
            "arialbd.ttf",
            "DejaVuSans-Bold.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        ]
    else:
        candidates = [
            "arial.ttf",
            "DejaVuSans.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        ]

    for candidate in candidates:
        try:
            return ImageFont.truetype(candidate, size=size)
        except Exception:
            continue

    return ImageFont.load_default()


def _fit_crop(image: Image.Image, target_width: int, target_height: int) -> Image.Image:
    source_ratio = image.width / image.height
    target_ratio = target_width / target_height

    if source_ratio > target_ratio:
        new_height = target_height
        new_width = int(new_height * source_ratio)
    else:
        new_width = target_width
        new_height = int(new_width / source_ratio)

    resized = image.resize((new_width, new_height), Image.LANCZOS)

    left = max((new_width - target_width) // 2, 0)
    top = max((new_height - target_height) // 2, 0)
    return resized.crop((left, top, left + target_width, top + target_height))


def generate_facebook_flyer(horse: Horse) -> None:
    if not horse.featured_photo:
        raise ValueError("Horse must have a featured photo before generating a flyer.")

    base = Image.new("RGB", (FLYER_WIDTH, FLYER_HEIGHT), "#f4efe7")
    draw = ImageDraw.Draw(base)

    photo = Image.open(horse.featured_photo.path).convert("RGB")
    photo = _fit_crop(photo, PHOTO_WIDTH, FLYER_HEIGHT)
    base.paste(photo, (0, 0))

    draw.rectangle(
        [(PHOTO_WIDTH, 0), (FLYER_WIDTH, FLYER_HEIGHT)],
        fill="#f7f1e8",
    )

    draw.rectangle(
        [(PHOTO_WIDTH, 0), (FLYER_WIDTH, 10)],
        fill="#5b3a1d",
    )

    title_font = _font(42, bold=True)
    big_font = _font(28, bold=True)
    body_font = _font(24, bold=False)
    small_font = _font(18, bold=False)
    label_font = _font(16, bold=True)

    x = PHOTO_WIDTH + 42
    y = 42

    draw.text((x, y), horse.program_id, fill="#6b5a45", font=label_font)
    y += 28

    draw.text((x, y), horse.barn_name.upper(), fill="#1f1a15", font=title_font)
    y += 64

    stats_line = f"{horse.age}yo | {horse.height_hands}h | {horse.get_sex_display()}"
    draw.text((x, y), stats_line, fill="#2d241c", font=body_font)
    y += 44

    focus_text = horse.get_discipline_focus_display()
    if horse.color:
        focus_text = f"{horse.color} | {focus_text}"
    draw.text((x, y), focus_text, fill="#2d241c", font=body_font)
    y += 56

    draw.text((x, y), "Price", fill="#6b5a45", font=label_font)
    y += 22

    if horse.price:
        price_text = f"${int(horse.price):,}"
    else:
        price_text = "INQUIRE"
    draw.text((x, y), price_text, fill="#2d241c", font=big_font)
    y += 68

    desc = (horse.description or "").strip()
    if desc:
        wrapped = []
        words = desc.split()
        line = ""
        for word in words:
            test = f"{line} {word}".strip()
            if draw.textlength(test, font=small_font) <= PANEL_WIDTH - 84:
                line = test
            else:
                wrapped.append(line)
                line = word
            if len(wrapped) >= 4:
                break
        if line and len(wrapped) < 4:
            wrapped.append(line)

        for wrapped_line in wrapped:
            draw.text((x, y), wrapped_line, fill="#4a4035", font=small_font)
            y += 28

        y += 16

    draw.text((x, FLYER_HEIGHT - 90), "Remus RodeoBred Thoroughbreds", fill="#1f1a15", font=label_font)
    draw.text((x, FLYER_HEIGHT - 62), "Tucson, Arizona", fill="#6b5a45", font=small_font)

    logo_candidates = [
        Path(horse._meta.app_config.path) / "static" / "images" / "rr_thoroughbreds_logo.png",
        Path(horse._meta.app_config.path) / "static" / "horses" / "images" / "rr_thoroughbreds_logo.png",
    ]
    logo_path = next((p for p in logo_candidates if p.exists()), None)

    if logo_path:
        try:
            logo = Image.open(logo_path).convert("RGBA")
            logo.thumbnail((130, 130), Image.LANCZOS)
            lx = FLYER_WIDTH - logo.width - 28
            ly = FLYER_HEIGHT - logo.height - 24
            base.paste(logo, (lx, ly), logo)
        except Exception:
            pass

    output = BytesIO()
    base.save(output, format="JPEG", quality=92)
    output.seek(0)

    filename = f"{horse.program_id.lower().replace(' ', '_')}_{horse.slug}_facebook.jpg"
    horse.flyer_image.save(filename, ContentFile(output.read()), save=True)


# ------------------------------
# TWILIO SMS HELPER
# ------------------------------

def send_sms(message: str, to_number: str):
    """
    Safe Twilio SMS sender.
    Will never crash the site if Twilio fails.
    """

    sid = getattr(settings, "TWILIO_ACCOUNT_SID", None)
    token = getattr(settings, "TWILIO_AUTH_TOKEN", None)
    phone = getattr(settings, "TWILIO_PHONE_NUMBER", None)

    if not sid or not token or not phone:
        return

    try:
        client = Client(sid, token)

        client.messages.create(
            body=message,
            from_=phone,
            to=to_number,
        )

    except Exception:
        pass