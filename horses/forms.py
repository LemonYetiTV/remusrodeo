# horses/forms.py
from django import forms

from .models import Inquiry


class InquiryForm(forms.ModelForm):
    class Meta:
        model = Inquiry
        fields = ["name", "email", "phone", "message"]
        widgets = {
            "name": forms.TextInput(attrs={
                "class": "form-input",
                "placeholder": "Your name",
            }),
            "email": forms.EmailInput(attrs={
                "class": "form-input",
                "placeholder": "you@example.com",
            }),
            "phone": forms.TextInput(attrs={
                "class": "form-input",
                "placeholder": "Phone number",
            }),
            "message": forms.Textarea(attrs={
                "class": "form-input",
                "placeholder": "Tell us what you are looking for, riding level, and any questions you have.",
                "rows": 5,
            }),
        }