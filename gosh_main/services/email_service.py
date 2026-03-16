import logging
import os

from django.conf import settings
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.urls import reverse

logger = logging.getLogger(__name__)


def _normalize_site_url() -> str:
    """Return site URL without trailing slash for consistent link building."""
    return (getattr(settings, 'SITE_URL', '') or 'http://localhost:8000').rstrip('/')


def _customer_tracking_dashboard_url() -> str:
    """Return absolute URL to the signed-in customer tracking dashboard."""
    return f"{_normalize_site_url()}{reverse('gosh_main:my_orders_tracking')}"


def _public_tracking_url(tracking_number: str) -> str:
    """Return absolute URL to a specific public tracking page."""
    return f"{_normalize_site_url()}{reverse('gosh_main:track_order_number', kwargs={'tracking_number': tracking_number})}"


def _get_sendgrid_api_key():
    return (os.environ.get('SENDGRID_API_KEY') or settings.EMAIL_HOST_PASSWORD or '').strip()


def _has_sendgrid_api_key():
    api_key = _get_sendgrid_api_key()
    return api_key.startswith('SG.') and len(api_key) > 20


def _log_sendgrid_smtp_configuration():
    if settings.EMAIL_HOST == 'smtp.sendgrid.net' and settings.EMAIL_HOST_USER != 'apikey':
        logger.error(
            "SendGrid SMTP is misconfigured: EMAIL_HOST_USER must be 'apikey', got %r",
            settings.EMAIL_HOST_USER,
        )


def _send_via_sendgrid(subject, body, to_email, reply_to=None):
    try:
        from sendgrid import SendGridAPIClient
        from sendgrid.helpers.mail import Mail, Email, To, Content
    except ImportError:
        logger.warning("sendgrid package not installed, falling back to SMTP")
        return False

    if not _has_sendgrid_api_key():
        logger.error(
            "SendGrid Web API is misconfigured: SENDGRID_API_KEY is missing or invalid. "
            "SendGrid API keys usually start with 'SG.'"
        )
        return False

    try:
        mail = Mail(
            from_email=Email(settings.DEFAULT_FROM_EMAIL),
            to_emails=To(to_email),
            subject=subject,
            plain_text_content=Content("text/plain", body),
        )
        if reply_to:
            mail.reply_to = Email(reply_to)

        response = SendGridAPIClient(_get_sendgrid_api_key()).send(mail)
        logger.info("Email sent via SendGrid Web API, status: %s", response.status_code)
        return True
    except Exception as error:
        logger.exception("SendGrid Web API request failed: %s", error)
        return False


def _send_via_smtp(subject, body, to_emails, reply_to=None):
    _log_sendgrid_smtp_configuration()

    try:
        email_message = EmailMessage(
            subject=subject,
            body=body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=to_emails,
            reply_to=[reply_to] if reply_to else None,
        )
        email_message.send(fail_silently=False)
        return True
    except Exception:
        logger.exception("SMTP/backend email send failed")
        return False


def send_contact_email(name, email, subject, message):
    """Send contact form email via SendGrid Web API (fallback to SMTP if package not available)"""
    if not subject:
        subject = "New contact message"

    body = (
        f"New contact message from {name} <{email}>\n\n"
        f"Subject: {subject}\n\n"
        f"{message}"
    )

    if _send_via_sendgrid(f"[Contact] {subject}", body, settings.CONTACT_EMAIL, reply_to=email):
        return True

    return _send_via_smtp(f"[Contact] {subject}", body, [settings.CONTACT_EMAIL], reply_to=email)


def send_password_reset_email(user_email, message_body, subject="Reset your Goshen password"):
    """Send password reset email via SendGrid Web API (fallback to SMTP)"""
    if _send_via_sendgrid(subject, message_body, user_email):
        return True

    return _send_via_smtp(subject, message_body, [user_email])


def send_email_verification_email(user_email, message_body, subject="Verify your Goshen account"):
    """Send account verification email via SendGrid Web API (fallback to SMTP)."""
    if _send_via_sendgrid(subject, message_body, user_email):
        return True

    return _send_via_smtp(subject, message_body, [user_email])


def send_order_confirmation_email(order):
    """
    Send order confirmation email to customer
    
    Args:
        order: Order instance
        
    Returns:
        bool: True if email sent successfully, False otherwise
    """
    try:
        # Get customer email
        if order.user and order.user.email:
            customer_email = order.user.email
        else:
            # Try to get email from payment record
            payment = order.payments.first()
            if payment and payment.payer_email:
                customer_email = payment.payer_email
            else:
                logger.warning(f"No email found for order {order.order_number}")
                return False
        
        # Render email template
        subject = f"Order Confirmation - {order.order_number}"
        
        # Build email body
        items_text = "\n".join([
            f"  - {item.product_name} x{item.quantity} @ ₦{item.product_price:,.2f} = ₦{item.line_total:,.2f}"
            for item in order.items.all()
        ])
        
        tracking_dashboard_url = _customer_tracking_dashboard_url()
        tracking = getattr(order, 'tracking', None)

        tracking_block = (
            f"Tracking Number: {tracking.tracking_number}\n"
            f"Track this order: {_public_tracking_url(tracking.tracking_number)}\n"
        ) if tracking else (
            "Tracking Number: Will be generated once your order is shipped.\n"
            f"Track from your dashboard: {tracking_dashboard_url}\n"
        )

        body = f"""
Dear {order.recipient_name},

Thank you for your order at Goshen Giant Food!

Order Details:
--------------
Order Number: {order.order_number}
Order Date: {order.created_at.strftime('%B %d, %Y at %I:%M %p')}
Payment Status: {order.get_payment_status_display()}

Items Ordered:
{items_text}

Subtotal: ₦{order.subtotal:,.2f}
Shipping: ₦{order.shipping_cost:,.2f}
Total: ₦{order.total:,.2f}

Delivery Address:
{order.recipient_name}
{order.address_line}
{order.city} {order.state}
{order.country}
Phone: {order.phone}

Tracking:
{tracking_block}

We'll send you another email when your order ships.

Thank you for shopping with us!

Best regards,
Goshen Giant Food Team
        """.strip()
        
        email_message = EmailMessage(
            subject=subject,
            body=body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[customer_email],
        )
        
        email_message.send(fail_silently=False)
        logger.info(f"Order confirmation email sent for order {order.order_number}")
        return True
        
    except Exception as e:
        logger.exception(f"Failed to send order confirmation email for order {order.order_number}: {str(e)}")
        return False


def send_order_tracking_email(order, tracking):
    """Send shipped/tracking email containing direct tracking URL and number."""
    try:
        if order.user and order.user.email:
            customer_email = order.user.email
        else:
            payment = order.payments.first()
            if payment and payment.payer_email:
                customer_email = payment.payer_email
            else:
                logger.warning(f"No email found for shipped order {order.order_number}")
                return False

        subject = f"Your Order Has Shipped - {order.order_number}"
        tracking_url = _public_tracking_url(tracking.tracking_number)
        dashboard_url = _customer_tracking_dashboard_url()

        body = f"""
Dear {order.recipient_name},

Good news. Your order is now on the way.

Order Number: {order.order_number}
Tracking Number: {tracking.tracking_number}
Current Status: {tracking.get_status_display()}

Track this order:
{tracking_url}

View all your orders:
{dashboard_url}

Delivery Address:
{order.recipient_name}
{order.address_line}
{order.city} {order.state}
{order.country}
Phone: {order.phone}

Thank you for shopping with us.

Best regards,
Goshen Giant Food Team
        """.strip()

        email_message = EmailMessage(
            subject=subject,
            body=body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[customer_email],
        )
        email_message.send(fail_silently=False)
        logger.info("Tracking email sent for order %s", order.order_number)
        return True
    except Exception as e:
        logger.exception("Failed to send tracking email for order %s: %s", order.order_number, str(e))
        return False


def send_newsletter_email(subject, message_body, recipients):
    """Send a newsletter message to a list of recipients."""
    recipients = [email.strip().lower() for email in recipients if email and email.strip()]
    if not recipients:
        return 0

    sent_count = 0

    # Newsletter sending should use SendGrid Web API only to avoid SMTP connectivity issues.
    try:
        from sendgrid import SendGridAPIClient
        from sendgrid.helpers.mail import Mail, Email, To, Content

        api_key = os.environ.get('SENDGRID_API_KEY') or settings.EMAIL_HOST_PASSWORD
        if not api_key:
            logger.error("SENDGRID_API_KEY is not configured; cannot send newsletter.")
            return 0

        sg = SendGridAPIClient(api_key)
        for recipient in recipients:
            try:
                mail = Mail(
                    from_email=Email(settings.DEFAULT_FROM_EMAIL),
                    to_emails=To(recipient),
                    subject=subject,
                    plain_text_content=Content("text/plain", message_body),
                )
                sg.send(mail)
                sent_count += 1
            except Exception as recipient_error:
                logger.exception(f"Failed to send newsletter email to {recipient}: {recipient_error}")

        return sent_count
    except ImportError:
        logger.error("sendgrid package not installed; cannot send newsletter.")
        return 0
    except Exception as e:
        logger.exception(f"SendGrid Web API newsletter send failed: {e}")
        return 0
