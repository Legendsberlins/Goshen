from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse


class EmailFailureFlowTests(TestCase):
    def test_register_deletes_inactive_user_when_verification_email_fails(self):
        with patch("gosh_main.views.send_email_verification_email", return_value=False):
            response = self.client.post(
                reverse("gosh_main:register"),
                {
                    "username": "newuser",
                    "email": "newuser@example.com",
                    "first_name": "New",
                    "last_name": "User",
                    "password": "Password1!",
                    "confirmation": "Password1!",
                },
            )

        self.assertContains(response, "We could not send the verification email")
        self.assertFalse(get_user_model().objects.filter(username="newuser").exists())

    def test_password_reset_stays_on_form_when_email_fails(self):
        user = get_user_model().objects.create_user(
            username="resetuser",
            email="reset@example.com",
            password="Password1!",
            is_active=True,
        )

        with patch("gosh_main.views.send_password_reset_email", return_value=False):
            response = self.client.post(
                reverse("gosh_main:password_reset_request"),
                {"email": user.email},
            )

        self.assertContains(response, "We could not send the password reset email")
