import os

from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from .forms import InquiryForm
from .models import Horse
from .utils import send_sms

def home(request):
    featured = Horse.objects.filter(
        is_published=True,
        is_featured=True,
    ).order_by("program_id")[:3]

    context = {
        "featured_horses": featured,
    }
    return render(request, "horses/home.html", context)


def horse_list(request):
    horses = Horse.objects.filter(
        is_published=True,
        is_for_sale=True,
        is_sold=False,
    ).order_by("program_id")

    context = {
        "horses": horses,
    }
    return render(request, "horses/horse_list.html", context)


def horse_detail(request, slug):
    horse = get_object_or_404(
        Horse,
        slug=slug,
        is_published=True,
    )

    updates = horse.training_updates.filter(is_published=True)
    gallery_photos = horse.photos.all()

    if request.method == "POST":
        form = InquiryForm(request.POST)
        if form.is_valid():
            inquiry = form.save(commit=False)
            inquiry.horse = horse
            inquiry.save()

            message = (
                f"Remus RodeoBred website inquiry\n"
                f"Horse: {horse.barn_name}\n"
                f"Name: {inquiry.name}\n"
                f"Phone: {inquiry.phone}\n"
                f"Message: {inquiry.message}\n"
                f"Listing: https://remusrodeo.com/horses/{horse.slug}/"
            )

            numbers = [
                os.environ.get("OWNER_ALERT_PHONE"),
                os.environ.get("TRAINER_ALERT_PHONE"),
            ]

            for number in numbers:
                if number:
                    send_sms(message, number)
            
            return redirect(
                reverse("horses:inquiry_success") + f"?horse={horse.program_id}"
            )
    else:
        form = InquiryForm()

    context = {
        "horse": horse,
        "updates": updates,
        "gallery_photos": gallery_photos,
        "form": form,
    }
    return render(request, "horses/horse_detail.html", context)


def sold_horses(request):
    horses = Horse.objects.filter(
        is_published=True,
        is_sold=True,
    ).order_by("-updated_at")

    context = {
        "horses": horses,
    }
    return render(request, "horses/sold_horses.html", context)


def inquiry_success(request):
    horse_program_id = request.GET.get("horse", "")

    context = {
        "horse_program_id": horse_program_id,
    }
    return render(request, "horses/inquiry_success.html", context)