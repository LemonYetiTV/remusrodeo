from django.contrib import admin, messages
from django.http import HttpResponseRedirect
from django.template.response import TemplateResponse
from django.urls import path, reverse
from django.utils.html import format_html

from .models import Horse, HorsePhoto, Inquiry, TrainingUpdate, HorseEvaluation
from .utils import generate_facebook_flyer


class HorsePhotoInline(admin.TabularInline):
    model = HorsePhoto
    extra = 1
    fields = ("image", "caption", "sort_order")
    ordering = ("sort_order",)


class TrainingUpdateInline(admin.StackedInline):
    model = TrainingUpdate
    extra = 0
    fields = ("title", "update_date", "body", "is_published")
    ordering = ("-update_date",)


class HorseEvaluationInline(admin.StackedInline):
    model = HorseEvaluation
    extra = 0
    max_num = 1
    can_delete = True
    fieldsets = (
        ("Intake Information", {
            "fields": (
                "arrival_date",
                "previous_owner",
                "purchase_source",
            )
        }),
        ("Condition & Temperament", {
            "fields": (
                "body_condition",
                "soundness_observations",
                "temperament_notes",
                "ground_manners",
                "handling_behavior",
            )
        }),
        ("Training Assessment", {
            "fields": (
                "training_level",
                "discipline_exposure",
                "behavioral_notes",
            )
        }),
        ("Care & Health Notes", {
            "fields": (
                "veterinary_notes",
                "farrier_status",
                "vaccination_status",
                "dental_status",
            )
        }),
    )


@admin.register(Horse)
class HorseAdmin(admin.ModelAdmin):
    change_form_template = "admin/horses/horse/change_form.html"

    list_display = (
        "program_id",
        "barn_name",
        "age",
        "sex",
        "discipline_focus",
        "training_stage",
        "price",
        "is_for_sale",
        "is_published",
        "is_sold",
        "is_new",
    )

    list_filter = (
        "sex",
        "discipline_focus",
        "training_stage",
        "is_for_sale",
        "is_published",
        "is_sold",
    )

    search_fields = (
        "program_id",
        "barn_name",
        "registered_name",
    )

    inlines = [
        HorseEvaluationInline,
        HorsePhotoInline,
        TrainingUpdateInline,
    ]
    @admin.register(HorseEvaluation)

    class HorseEvaluationAdmin(admin.ModelAdmin):
        list_display = ("horse", "arrival_date", "created_at", "updated_at")
        search_fields = ("horse__program_id", "horse__barn_name", "previous_owner", "purchase_source")
        ordering = ("-updated_at",)

    def get_readonly_fields(self, request, obj=None):
        base_fields = ("created_at", "updated_at", "is_new", "flyer_preview")
        if obj:
            return ("program_id", "slug", *base_fields)
        return base_fields

    fieldsets = (
        ("Identity", {
            "fields": (
                "program_id",
                "slug",
                "barn_name",
                "registered_name",
            )
        }),
        ("Basic Info", {
            "fields": (
                "age",
                "height_hands",
                "sex",
                "color",
            )
        }),
        ("Training", {
            "fields": (
                "discipline_focus",
                "training_stage",
                "temperament",
                "description",
                "track_notes",
                "youtube_url",
            )
        }),
        ("Sales", {
            "fields": (
                "price",
                "is_for_sale",
                "is_sold",
                "is_published",
                "is_featured",
                "is_new",
            )
        }),
        ("Media", {
            "fields": (
                "featured_photo",
                "flyer_image",
                "flyer_preview",
            )
        }),
        ("Dates", {
            "fields": (
                "date_acquired",
                "created_at",
                "updated_at",
            )
        }),
    )

    def flyer_preview(self, obj):
        if obj and obj.flyer_image:
            return format_html(
                '<a href="{}" target="_blank">Download current flyer</a>',
                obj.flyer_image.url,
            )
        return "No flyer generated yet."

    flyer_preview.short_description = "Flyer Preview"

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                "<path:object_id>/generate-flyer/",
                self.admin_site.admin_view(self.generate_flyer_view),
                name="horses_horse_generate_flyer",
            ),
            path(
                "<path:object_id>/facebook-post/",
                self.admin_site.admin_view(self.facebook_post_view),
                name="horses_horse_facebook_post",
            ),
        ]
        return custom_urls + urls

    def render_change_form(self, request, context, *args, **kwargs):
        obj = context.get("original")
        if obj:
            context["generate_flyer_url"] = reverse(
                "admin:horses_horse_generate_flyer",
                args=[obj.pk],
            )
            context["facebook_post_url"] = reverse(
                "admin:horses_horse_facebook_post",
                args=[obj.pk],
            )
        return super().render_change_form(request, context, *args, **kwargs)

    def generate_flyer_view(self, request, object_id):
        horse = self.get_object(request, object_id)
        if not horse:
            self.message_user(request, "Horse not found.", level=messages.ERROR)
            return HttpResponseRedirect(reverse("admin:horses_horse_changelist"))

        try:
            generate_facebook_flyer(horse)
            self.message_user(request, "Flyer generated successfully.", level=messages.SUCCESS)
        except Exception as exc:
            self.message_user(request, f"Flyer generation failed: {exc}", level=messages.ERROR)

        return HttpResponseRedirect(
            reverse("admin:horses_horse_change", args=[horse.pk])
        )

    def facebook_post_view(self, request, object_id):
        horse = self.get_object(request, object_id)
        if not horse:
            self.message_user(request, "Horse not found.", level=messages.ERROR)
            return HttpResponseRedirect(reverse("admin:horses_horse_changelist"))

        listing_url = request.build_absolute_uri(horse.get_absolute_url())

        post_text = f"""{horse.program_id} | {horse.barn_name}

{horse.age}yo | {horse.height_hands}h | {horse.get_sex_display()}
{horse.color + " | " if horse.color else ""}{horse.get_discipline_focus_display()}

{"$" + format(int(horse.price), ",") if horse.price else "Price on request"}
Tucson, AZ

Video + Details:
{listing_url}"""

        context = {
            **self.admin_site.each_context(request),
            "opts": self.model._meta,
            "original": horse,
            "title": f"Facebook post text for {horse.program_id}",
            "post_text": post_text,
        }

        return TemplateResponse(
            request,
            "admin/horses/horse/facebook_post.html",
            context,
        )


@admin.register(HorsePhoto)
class HorsePhotoAdmin(admin.ModelAdmin):
    list_display = ("horse", "caption", "sort_order", "uploaded_at")
    list_filter = ("horse",)
    ordering = ("horse", "sort_order")


@admin.register(TrainingUpdate)
class TrainingUpdateAdmin(admin.ModelAdmin):
    list_display = ("horse", "title", "update_date", "is_published")
    list_filter = ("horse", "is_published")
    search_fields = ("horse__program_id", "title")
    ordering = ("-update_date",)


@admin.register(Inquiry)
class InquiryAdmin(admin.ModelAdmin):
    list_display = ("name", "horse", "email", "phone", "created_at", "is_contacted")
    list_filter = ("is_contacted", "created_at")
    search_fields = (
        "name",
        "email",
        "phone",
        "message",
        "horse__program_id",
        "horse__barn_name",
    )
    ordering = ("-created_at",)