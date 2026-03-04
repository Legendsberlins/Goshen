from django.core.management.base import BaseCommand

from gosh_main.models import NewsletterSignup
from gosh_main.services.email_service import send_newsletter_email


class Command(BaseCommand):
    help = "Send a newsletter email to all subscribed users"

    def add_arguments(self, parser):
        parser.add_argument("--subject", required=True, help="Newsletter subject")
        parser.add_argument("--message", required=True, help="Newsletter message body")
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show subscriber count without sending emails",
        )

    def handle(self, *args, **options):
        subject = options["subject"].strip()
        message = options["message"].strip()
        dry_run = options["dry_run"]

        recipients = list(
            NewsletterSignup.objects.order_by("email").values_list("email", flat=True)
        )

        if not recipients:
            self.stdout.write(self.style.WARNING("No newsletter subscribers found."))
            return

        self.stdout.write(f"Found {len(recipients)} subscriber(s).")

        if dry_run:
            self.stdout.write(self.style.SUCCESS("Dry run complete. No emails were sent."))
            return

        sent_count = send_newsletter_email(subject, message, recipients)

        if sent_count == len(recipients):
            self.stdout.write(
                self.style.SUCCESS(f"Newsletter sent successfully to {sent_count} subscriber(s).")
            )
        else:
            self.stdout.write(
                self.style.WARNING(
                    f"Newsletter sent to {sent_count}/{len(recipients)} subscriber(s). Check logs for failures."
                )
            )
