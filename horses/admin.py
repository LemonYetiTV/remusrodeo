from django.contrib import admin, messages
from django.contrib.auth.admin import GroupAdmin, UserAdmin
from django.contrib.auth.models import Group, Permission, User
from django.contrib.contenttypes.models import ContentType
from django.db.models.signals import post_migrate
from django.dispatch import receiver
from django.http import HttpResponseRedirect
from django.template.response import TemplateResponse
from django.urls import path, reverse
from django.utils.html import format_html

from .models import Horse, HorseEvaluation, HorsePhoto, Inquiry, TrainingUpdate
from .utils import generate_facebook_flyer

admin.site.site_header = "Remus Rodeo"
admin.site.site_title = "Stable Management Hub"
admin.site.index_title = "Stable Management Hub"

TRAINER_GROUP_NAME = "TrainerGroup"


def _is_superuser(request):
    return bool(request.user and request.user.is_active and request.user.is_superuser)


class AdminBrandingMixin:
    class Media:
        css = {
            "all": ("admin/css/remus_admin.css",)
        }


class TrainerVisibleAdminMixin:
    def has_module_permission(self, request):
        if _is_superuser(request):
            return True
        return bool(request.user and request.user.is_active and request.user.is_staff)

    def has_view_permission(self, request, obj=None):
        if _is_superuser(request):
            return True
        return super().has_view_permission(request, obj)

    def has_add_permission(self, request):
        if _is_superuser(request):
            return True
        return super().has_add_permission(request)

    def has_change_permission(self, request, obj=None):
        if _is_superuser(request):
            return True
        return super().has_change_permission(request, obj)

    def has_delete_permission(self, request, obj=None):
        if _is_superuser(request):
            return True
        return super().has_delete_permission(request, obj)


class SuperuserOnlyAdminMixin:
    def has_module_permission(self, request):
        return _is_superuser(request)

    def has_view_permission(self, request, obj=None):
        return _is_superuser(request)

    def has_add_permission(self, request):
        return _is_superuser(request)

    def has_change_permission(self, request, obj=None):
        return _is_superuser(request)

    def has_delete_permission(self, request, obj=None):
        return _is_superuser(request)


class HorsePhotoInline(admin.TabularInline):
    model = HorsePhoto
    extra = 1
    fields = ("image", "caption", "sort_order")
    ordering = ("sort_order",)

    def has_view_permission(self, request, obj=None):
        if _is_superuser(request):
            return True
        return super().has_view_permission(request, obj)

    def has_add_permission(self, request, obj=None):
        if _is_superuser(request):
            return True
        return super().has_add_permission(request, obj)

    def has_change_permission(self, request, obj=None):
        if _is_superuser(request):
            return True
        return super().has_change_permission(request, obj)

    def has_delete_permission(self, request, obj=None):
        if _is_superuser(request):
            return True
        return super().has_delete_permission(request, obj)


class TrainingUpdateInline(admin.StackedInline):
    model = TrainingUpdate
    extra = 0
    fields = ("title", "update_date", "body", "is_published")
    ordering = ("-update_date",)

    def has_view_permission(self, request, obj=None):
        if _is_superuser(request):
            return True
        return super().has_view_permission(request, obj)

    def has_add_permission(self, request, obj=None):
        if _is_superuser(request):
            return True
        return super().has_add_permission(request, obj)

    def has_change_permission(self, request, obj=None):
        if _is_superuser(request):
            return True
        return super().has_change_permission(request, obj)

    def has_delete_permission(self, request, obj=None):
        if _is_superuser(request):
            return True
        return super().has_delete_permission(request, obj)


class HorseEvaluationInline(admin.StackedInline):
    model = HorseEvaluation
    extra = 0
    max_num = 1
    can_delete = True
    fieldsets = (
        (
            "Intake Information",
            {
                "fields": (
                    "arrival_date",
                    "previous_owner",
                    "purchase_source",
                )
            },
        ),
        (
            "Condition & Temperament",
            {
                "fields": (
                    "body_condition",
                    "soundness_observations",
                    "temperament_notes",
                    "ground_manners",
                    "handling_behavior",
                )
            },
        ),
        (
            "Training Assessment",
            {
                "fields": (
                    "training_level",
                    "discipline_exposure",
                    "behavioral_notes",
                )
            },
        ),
        (
            "Care & Health Notes",
            {
                "fields": (
                    "veterinary_notes",
                    "farrier_status",
                    "vaccination_status",
                    "dental_status",
                )
            },
        ),
    )

    def has_view_permission(self, request, obj=None):
        if _is_superuser(request):
            return True
        return super().has_view_permission(request, obj)

    def has_add_permission(self, request, obj=None):
        if _is_superuser(request):
            return True
        return super().has_add_permission(request, obj)

    def has_change_permission(self, request, obj=None):
        if _is_superuser(request):
            return True
        return super().has_change_permission(request, obj)

    def has_delete_permission(self, request, obj=None):
        if _is_superuser(request):
            return True
        return super().has_delete_permission(request, obj)


@admin.register(Horse)
class HorseAdmin(AdminBrandingMixin, TrainerVisibleAdminMixin, admin.ModelAdmin):
    change_form_template = "admin/horses/horse/change_form.html"

    list_display = (
        "program_id",
        "barn_name",
        "age",
        "sex",
        "discipline_focus",
        "training_stage",
        "formatted_price",
        "sale_status_badge",
        "publish_status_badge",
        "photo_thumb",
        "quick_actions",
)

    list_display_links = ("photo_thumb", "program_id", "barn_name")
    list_filter = (
        "sex",
        "discipline_focus",
        "training_stage",
        "is_for_sale",
        "is_published",
        "is_sold",
        "is_featured",
    )
    search_fields = (
        "program_id",
        "barn_name",
        "registered_name",
    )
    list_per_page = 25

    inlines = [
        HorseEvaluationInline,
        HorsePhotoInline,
        TrainingUpdateInline,
    ]

    fieldsets = (
        (
            "Identity",
            {
                "fields": (
                    "program_id",
                    "slug",
                    "barn_name",
                    "registered_name",
                )
            },
        ),
        (
            "Basic Info",
            {
                "fields": (
                    "age",
                    "height_hands",
                    "sex",
                    "color",
                )
            },
        ),
        (
            "Training",
            {
                "fields": (
                    "discipline_focus",
                    "training_stage",
                    "temperament",
                    "description",
                    "track_notes",
                    "youtube_url",
                )
            },
        ),
        (
            "Sales",
            {
                "fields": (
                    "price",
                    "is_for_sale",
                    "is_sold",
                    "is_published",
                    "is_featured",
                    "is_new",
                )
            },
        ),
        (
            "Media",
            {
                "fields": (
                    "featured_photo",
                )
            },
        ),
        (
            "Dates",
            {
                "fields": (
                    "date_acquired",
                    "created_at",
                    "updated_at",
                )
            },
        ),
    )

    def get_readonly_fields(self, request, obj=None):
        base_fields = ("created_at", "updated_at", "is_new",)
        if obj:
            return ("program_id", "slug", *base_fields)
        return base_fields

    def photo_thumb(self, obj):
        image = getattr(obj, "featured_photo", None)

        if not image:
            return format_html(
                '<div style="width:72px;height:72px;display:flex;align-items:center;justify-content:center;'
                'border:1px dashed #9ca3af;border-radius:10px;color:#6b7280;font-size:11px;">{}</div>',
                "No Photo",
            )

        try:
            image_url = image.url
        except Exception:
            return format_html(
                '<div style="width:72px;height:72px;display:flex;align-items:center;justify-content:center;'
                'border:1px dashed #9ca3af;border-radius:10px;color:#6b7280;font-size:11px;">{}</div>',
                "Bad Image",
            )

        return format_html(
            '<img src="{}" style="width:72px;height:72px;object-fit:cover;border-radius:10px;border:1px solid #d1d5db;" />',
            image_url,
        )

        photo_thumb.short_description = "Photo"

    def formatted_price(self, obj):
        if obj.price is None:
            return "Price on request"

        try:
            return f"${int(obj.price):,}"
        except (TypeError, ValueError):
            return str(obj.price)

    formatted_price.short_description = "Price"
    formatted_price.admin_order_field = "price"

    def sale_status_badge(self, obj):
        if obj.is_sold:
            label = "Sold"
            bg = "#991b1b"
            fg = "#ffffff"
        elif obj.is_for_sale:
            label = "For Sale"
            bg = "#166534"
            fg = "#ffffff"
        else:
            label = "Not Listed"
            bg = "#6b7280"
            fg = "#ffffff"

        return format_html(
            '<span style="display:inline-block;padding:4px 10px;border-radius:999px;'
            'background:{};color:{};font-weight:600;font-size:12px;">{}</span>',
            bg,
            fg,
            label,
        )

    sale_status_badge.short_description = "Sale Status"

    def publish_status_badge(self, obj):
        if obj.is_published:
            label = "Published"
            bg = "#1d4ed8"
            fg = "#ffffff"
        else:
            label = "Draft"
            bg = "#92400e"
            fg = "#ffffff"

        return format_html(
            '<span style="display:inline-block;padding:4px 10px;border-radius:999px;'
            'background:{};color:{};font-weight:600;font-size:12px;">{}</span>',
            bg,
            fg,
            label,
        )

    publish_status_badge.short_description = "Publish Status"

    def quick_actions(self, obj):
        edit_url = reverse("admin:horses_horse_change", args=[obj.pk])
        flyer_url = reverse("admin:horses_horse_generate_flyer", args=[obj.pk])
        facebook_url = reverse("admin:horses_horse_facebook_post", args=[obj.pk])

        return format_html(
            '<div style="display:flex;gap:6px;flex-wrap:wrap;">'
            '<a class="button" href="{}">Edit</a>'
            '<a class="button" href="{}">Flyer</a>'
            '<a class="button" href="{}">Post</a>'
            "</div>",
            edit_url,
            flyer_url,
            facebook_url,
        )

    quick_actions.short_description = "Actions"

    def flyer_preview(self, obj):
        if not obj:
            return "No flyer generated yet."

        flyer = getattr(obj, "flyer_image", None)
        if not flyer:
            return "No flyer generated yet."

        try:
            flyer_url = flyer.url
        except Exception:
            return "Flyer file unavailable."

        return format_html(
            '<a href="{}" target="_blank" rel="noopener noreferrer">{}</a>',
            flyer_url,
            "Download current flyer",
        )

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

        if not self.has_change_permission(request, horse):
            self.message_user(
                request,
                "You do not have permission to generate a flyer for this horse.",
                level=messages.ERROR,
            )
            return HttpResponseRedirect(reverse("admin:horses_horse_changelist"))

        try:
            generate_facebook_flyer(horse)
            self.message_user(
                request,
                "Flyer generated successfully.",
                level=messages.SUCCESS,
            )
        except Exception as exc:
            self.message_user(
                request,
                f"Flyer generation failed: {exc}",
                level=messages.ERROR,
            )

        return HttpResponseRedirect(
            reverse("admin:horses_horse_change", args=[horse.pk])
        )

    def facebook_post_view(self, request, object_id):
        horse = self.get_object(request, object_id)
        if not horse:
            self.message_user(request, "Horse not found.", level=messages.ERROR)
            return HttpResponseRedirect(reverse("admin:horses_horse_changelist"))

        if not self.has_view_permission(request, horse):
            self.message_user(
                request,
                "You do not have permission to view this horse.",
                level=messages.ERROR,
            )
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
class HorsePhotoAdmin(AdminBrandingMixin, TrainerVisibleAdminMixin, admin.ModelAdmin):
    list_display = ("photo_preview", "horse", "caption", "sort_order", "uploaded_at")
    list_display_links = ("photo_preview", "horse")
    list_filter = ("horse",)
    search_fields = ("horse__program_id", "horse__barn_name", "caption")
    ordering = ("horse", "sort_order")

    def photo_preview(self, obj):
        image = getattr(obj, "image", None)

        if not image:
            return format_html(
                '<div style="width:60px;height:60px;display:flex;align-items:center;justify-content:center;'
                'border:1px dashed #9ca3af;border-radius:8px;color:#6b7280;font-size:10px;">{}</div>',
                "No Image",
            )

        try:
            image_url = image.url
        except Exception:
            return format_html(
                '<div style="width:60px;height:60px;display:flex;align-items:center;justify-content:center;'
                'border:1px dashed #9ca3af;border-radius:8px;color:#6b7280;font-size:10px;">{}</div>',
                "Bad Image",
            )

        return format_html(
            '<img src="{}" style="width:60px;height:60px;object-fit:cover;border-radius:8px;border:1px solid #d1d5db;" />',
            image_url,
        )

        photo_preview.short_description = "Image"


@admin.register(TrainingUpdate)
class TrainingUpdateAdmin(AdminBrandingMixin, TrainerVisibleAdminMixin, admin.ModelAdmin):
    list_display = ("horse", "title", "update_date", "publish_badge")
    list_filter = ("horse", "is_published")
    search_fields = ("horse__program_id", "horse__barn_name", "title")
    ordering = ("-update_date",)

    def publish_badge(self, obj):
        if obj.is_published:
            return format_html(
                '<span style="display:inline-block;padding:4px 10px;border-radius:999px;'
                'background:#1d4ed8;color:#ffffff;font-weight:600;font-size:12px;">{}</span>',
                "Published",
            )
        return format_html(
            '<span style="display:inline-block;padding:4px 10px;border-radius:999px;'
            'background:#92400e;color:#ffffff;font-weight:600;font-size:12px;">{}</span>',
            "Draft",
        )

    publish_badge.short_description = "Status"
    publish_badge.admin_order_field = "is_published"


@admin.register(HorseEvaluation)
class HorseEvaluationAdmin(AdminBrandingMixin, TrainerVisibleAdminMixin, admin.ModelAdmin):
    list_display = ("horse", "arrival_date", "created_at", "updated_at")
    search_fields = (
        "horse__program_id",
        "horse__barn_name",
        "previous_owner",
        "purchase_source",
    )
    ordering = ("-updated_at",)


@admin.register(Inquiry)
class InquiryAdmin(AdminBrandingMixin, SuperuserOnlyAdminMixin, admin.ModelAdmin):
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


try:
    admin.site.unregister(User)
except admin.sites.NotRegistered:
    pass

try:
    admin.site.unregister(Group)
except admin.sites.NotRegistered:
    pass


class RestrictedUserAdmin(AdminBrandingMixin, SuperuserOnlyAdminMixin, UserAdmin):
    pass


class RestrictedGroupAdmin(AdminBrandingMixin, SuperuserOnlyAdminMixin, GroupAdmin):
    pass


admin.site.register(User, RestrictedUserAdmin)
admin.site.register(Group, RestrictedGroupAdmin)


@receiver(post_migrate)
def ensure_trainer_group(sender, **kwargs):
    group, _ = Group.objects.get_or_create(name=TRAINER_GROUP_NAME)

    model_permission_map = {
        Horse: {"view_horse", "add_horse", "change_horse"},
        HorsePhoto: {"view_horsephoto", "add_horsephoto", "change_horsephoto"},
        TrainingUpdate: {
            "view_trainingupdate",
            "add_trainingupdate",
            "change_trainingupdate",
        },
        HorseEvaluation: {
            "view_horseevaluation",
            "add_horseevaluation",
            "change_horseevaluation",
        },
    }

    permission_ids = []
    for model, codenames in model_permission_map.items():
        content_type = ContentType.objects.get_for_model(model)
        perms = Permission.objects.filter(
            content_type=content_type,
            codename__in=codenames,
        )
        permission_ids.extend(perms.values_list("id", flat=True))

    group.permissions.set(permission_ids)
