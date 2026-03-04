from django import forms
from django.contrib.auth import get_user_model

UserModel = get_user_model()


class PasswordResetRequestForm(forms.Form):
    email = forms.EmailField(
        label="Email address",
        widget=forms.EmailInput(attrs={"autocomplete": "email"})
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user_cache = None

    def clean_email(self):
        email = self.cleaned_data.get("email", "").strip()
        user = UserModel.objects.filter(email__iexact=email).first()
        if not user:
            raise forms.ValidationError("No account found with that email address.")
        self.user_cache = user
        return email

    def get_user(self):
        return self.user_cache
