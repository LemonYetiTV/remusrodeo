from __future__ import annotations

import re
from datetime import timedelta
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.text import slugify


MAX_FEATURED_PHOTO_MB = 5
NEW_LISTING_DAYS = 30


def validate_featured_photo_size(image):
    if not image:
        return

    max_bytes = MAX_FEATURED_PHOTO_MB * 1024 * 1024
    if image.size > max_bytes:
        raise ValidationError(
            f"Featured photo must be {MAX_FEATURED_PHOTO_MB} MB or smaller."
        )


class Horse(models.Model):
    class Sex(models.TextChoices):
        GELDING = "gelding", "Gelding"
        MARE = "mare", "Mare"
        STALLION = "stallion", "Stallion"

    class DisciplineFocus(models.TextChoices):
        BARRELS = "barrels", "Barrels"
        POLES = "poles", "Poles"
        ALL_AROUND = "all_around", "All Around"
        GYMKHANA = "gymkhana", "Gymkhana"
        RODEO_PROSPECT = "rodeo_prospect", "Rodeo Prospect"

    class TrainingStage(models.TextChoices):
        EVALUATION = "evaluation", "Evaluation"
        DECOMPRESSION = "decompression", "Decompression"
        RESTART_FOUNDATION = "restart_foundation", "Restart Foundation"
        PATTERN_INTRO = "pattern_intro", "Pattern Introduction"
        STARTED_ON_PATTERN = "started_on_pattern", "Started on Pattern"
        EXHIBITIONING = "exhibitioning", "Exhibitioning"
        FOR_SALE = "for_sale", "For Sale"
        SOLD = "sold", "Sold"

    program_id = models.CharField(
        max_length=20,
        unique=True,
        blank=True,
        help_text="Auto-generated if left blank, e.g. RRB-001",
    )
    slug = models.SlugField(
        max_length=120,
        unique=True,
        blank=True,
        help_text="Auto-generated from program ID and barn name for public URLs",
    )

    barn_name = models.CharField(max_length=100)
    registered_name = models.CharField(max_length=150, blank=True)

    age = models.PositiveIntegerField(
        validators=[MinValueValidator(1)],
        help_text="Horse age in years",
    )
    height_hands = models.DecimalField(
        max_digits=4,
        decimal_places=1,
        validators=[MinValueValidator(Decimal("0.1"))],
        help_text="Example: 15.3",
    )

    sex = models.CharField(
        max_length=20,
        choices=Sex.choices,
        default=Sex.GELDING,
    )
    color = models.CharField(max_length=50, blank=True)

    discipline_focus = models.CharField(
        max_length=30,
        choices=DisciplineFocus.choices,
        default=DisciplineFocus.RODEO_PROSPECT,
    )
    training_stage = models.CharField(
        max_length=30,
        choices=TrainingStage.choices,
        default=TrainingStage.EVALUATION,
    )

    temperament = models.CharField(
        max_length=255,
        blank=True,
        help_text="Short summary like 'quiet, willing, quick-footed'",
    )

    description = models.TextField(
        blank=True,
        help_text="Public-facing sale or profile description",
    )
    track_notes = models.TextField(
        blank=True,
        help_text="Private/internal notes from track evaluation or intake",
    )

    youtube_url = models.URLField(
        blank=True,
        help_text="Optional YouTube link for longer-form horse video",
    )

    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        blank=True,
        null=True,
        validators=[MinValueValidator(Decimal("0.00"))],
    )

    is_for_sale = models.BooleanField(default=False)
    is_published = models.BooleanField(default=False)
    is_sold = models.BooleanField(default=False)
    is_featured = models.BooleanField(default=False)

    date_acquired = models.DateField(blank=True, null=True)

    featured_photo = models.ImageField(
        upload_to="horses/featured/",
        blank=True,
        null=True,
        validators=[validate_featured_photo_size],
        help_text=f"Featured photo must be {MAX_FEATURED_PHOTO_MB} MB or smaller.",
    )

    flyer_image = models.ImageField(
        upload_to="flyers/",
        blank=True,
        null=True,
        help_text="Auto-generated Facebook flyer image.",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["program_id"]

    def __str__(self) -> str:
        return f"{self.program_id} - {self.barn_name}"

    @staticmethod
    def _next_program_id() -> str:
        existing_ids = Horse.objects.values_list("program_id", flat=True)
        pattern = re.compile(r"^RRB-(\d{3,})$")

        max_num = 0
        for value in existing_ids:
            if not value:
                continue
            match = pattern.match(value)
            if match:
                max_num = max(max_num, int(match.group(1)))

        return f"RRB-{max_num + 1:03d}"

    @property
    def is_new(self) -> bool:
        if not self.created_at:
            return False

        cutoff = timezone.now() - timedelta(days=NEW_LISTING_DAYS)
        return self.created_at >= cutoff

    @property
    def youtube_embed_url(self) -> str:
        if not self.youtube_url:
            return ""

        url = self.youtube_url.strip()

        patterns = [
            r"(?:youtube\.com/watch\?v=)([\w-]{11})",
            r"(?:youtu\.be/)([\w-]{11})",
            r"(?:youtube\.com/embed/)([\w-]{11})",
            r"(?:youtube\.com/shorts/)([\w-]{11})",
        ]

        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                video_id = match.group(1)
                return f"https://www.youtube.com/embed/{video_id}"

        return ""

    def save(self, *args, **kwargs):
        if not self.program_id:
            self.program_id = self._next_program_id()

        if not self.slug:
            base = f"{self.program_id}-{self.barn_name}".strip("-")
            self.slug = slugify(base)

        if self.is_sold:
            self.is_for_sale = False
            self.training_stage = self.TrainingStage.SOLD
        elif self.is_for_sale and self.training_stage != self.TrainingStage.SOLD:
            self.training_stage = self.TrainingStage.FOR_SALE

        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("horses:horse_detail", kwargs={"slug": self.slug})


class HorsePhoto(models.Model):
    horse = models.ForeignKey(
        Horse,
        on_delete=models.CASCADE,
        related_name="photos",
    )
    image = models.ImageField(upload_to="horses/gallery/")
    caption = models.CharField(max_length=255, blank=True)
    sort_order = models.PositiveIntegerField(default=0)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["sort_order", "id"]

    def __str__(self) -> str:
        return f"Photo for {self.horse.program_id}"


class TrainingUpdate(models.Model):
    horse = models.ForeignKey(
        Horse,
        on_delete=models.CASCADE,
        related_name="training_updates",
    )
    title = models.CharField(max_length=150)
    update_date = models.DateField()
    body = models.TextField()
    is_published = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-update_date", "-id"]

    def __str__(self) -> str:
        return f"{self.horse.program_id} - {self.title}"


class Inquiry(models.Model):
    horse = models.ForeignKey(
        Horse,
        on_delete=models.SET_NULL,
        related_name="inquiries",
        blank=True,
        null=True,
    )
    name = models.CharField(max_length=120)
    email = models.EmailField()
    phone = models.CharField(max_length=30, blank=True)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_contacted = models.BooleanField(default=False)

    class Meta:
        ordering = ["-created_at"]
        verbose_name_plural = "Inquiries"

    def __str__(self) -> str:
        horse_ref = self.horse.program_id if self.horse else "General Inquiry"
        return f"{self.name} - {horse_ref}"