# horses/urls.py
from django.urls import path

from . import views

app_name = "horses"

urlpatterns = [
    path("", views.home, name="home"),
    path("horses/", views.horse_list, name="horse_list"),
    path("horses/sold/", views.sold_horses, name="sold_horses"),
    path("horses/inquiry/success/", views.inquiry_success, name="inquiry_success"),
    path("horses/<slug:slug>/", views.horse_detail, name="horse_detail"),
]