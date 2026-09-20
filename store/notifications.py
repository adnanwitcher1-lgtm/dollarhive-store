"""
store/notifications.py
-----------------------
All "someone just placed an order" notification logic lives here, kept
separate from views.py so checkout stays readable. Three triggers fire
when an order is placed (see views.checkout):

    1. send_customer_confirmation_email(order)  -> email to the buyer
    2. send_merchant_alert_email(order)         -> email to the store owner
    3. send_whatsapp_order_notifications(order) -> WhatsApp to buyer + owner

`notify_new_order(order)` runs all three and is the single function
views.py needs to call.

WhatsApp uses the Twilio WhatsApp Business API. Install the SDK with:
    pip install twilio
and set TWILIO_ACCOUNT_SID / TWILIO_AUTH_TOKEN / TWILIO_WHATSAPP_FROM /
MERCHANT_WHATSAPP_NUMBER in settings.py (see settings.py comments).
If Twilio isn't configured (e.g. in local dev), WhatsApp sending is
skipped gracefully and logged instead of raising.
"""
import logging
import threading

from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string

logger = logging.getLogger(__name__)


# ----------------------------------------------------------------------
# 1. Customer order confirmation email
# ----------------------------------------------------------------------
def send_customer_confirmation_email(order):
    """
    Emails the customer their order confirmation: items purchased,
    total amount, and shipping information.
    """
    subject = f'SK Mart — Your order #{order.pk} is confirmed 🎉'
    message = render_to_string('store/emails/customer_confirmation.txt', {
        'order': order,
    })

    try:
        sent_count = send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[order.customer_email],
            fail_silently=settings.NOTIFICATIONS_FAIL_SILENTLY,
        )
        # send_mail() with fail_silently=True does NOT raise on failure —
        # it just returns 0. Without checking this, a failed send was
        # being logged (and treated) as a success.
        if sent_count:
            logger.info('Customer confirmation email sent for order #%s', order.pk)
            return True
        logger.warning(
            'Customer confirmation email NOT sent for order #%s (send_mail returned 0 — '
            'check EMAIL_HOST_USER/EMAIL_HOST_PASSWORD env vars on Render)',
            order.pk,
        )
        return False
    except Exception:
        logger.exception('Failed to send customer confirmation email for order #%s', order.pk)
        if not settings.NOTIFICATIONS_FAIL_SILENTLY:
            raise
        return False


# ----------------------------------------------------------------------
# 2. Merchant / store-admin new-order alert email
# ----------------------------------------------------------------------
def send_merchant_alert_email(order):
    """
    Emails the store administrator (settings.MERCHANT_EMAIL) the moment
    a new order comes in, so it can be picked, packed, and shipped.
    """
    subject = f'🛎️ New SK Mart order #{order.pk} — Rs {order.order_total}'
    message = render_to_string('store/emails/merchant_alert.txt', {
        'order': order,
    })

    try:
        sent_count = send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[settings.MERCHANT_EMAIL],
            fail_silently=settings.NOTIFICATIONS_FAIL_SILENTLY,
        )
        if sent_count:
            logger.info('Merchant alert email sent for order #%s', order.pk)
            return True
        logger.warning(
            'Merchant alert email NOT sent for order #%s (send_mail returned 0 — '
            'check EMAIL_HOST_USER/EMAIL_HOST_PASSWORD env vars on Render)',
            order.pk,
        )
        return False
    except Exception:
        logger.exception('Failed to send merchant alert email for order #%s', order.pk)
        if not settings.NOTIFICATIONS_FAIL_SILENTLY:
            raise
        return False


# ----------------------------------------------------------------------
# 3. WhatsApp order notifications (Twilio WhatsApp Business API)
# ----------------------------------------------------------------------
def _get_twilio_client():
    """
    Lazily builds a Twilio client. Returns None if the `twilio` package
    isn't installed or credentials aren't configured, so WhatsApp
    sending can be skipped gracefully instead of crashing checkout.
    """
    if not settings.TWILIO_ACCOUNT_SID or not settings.TWILIO_AUTH_TOKEN:
        logger.warning('Twilio credentials not configured — skipping WhatsApp notification.')
        return None

    try:
        from twilio.rest import Client
    except ImportError:
        logger.warning('The "twilio" package is not installed (pip install twilio) — skipping WhatsApp notification.')
        return None

    return Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)


def _send_whatsapp_message(client, to_number, body):
    """Sends a single WhatsApp message via Twilio. `to_number` should
    be in E.164 format, e.g. +923001234567 — the 'whatsapp:' prefix is
    added automatically."""
    if not to_number:
        return False

    to_whatsapp = to_number if to_number.startswith('whatsapp:') else f'whatsapp:{to_number}'

    try:
        client.messages.create(
            from_=settings.TWILIO_WHATSAPP_FROM,
            to=to_whatsapp,
            body=body,
        )
        return True
    except Exception:
        logger.exception('Failed to send WhatsApp message to %s', to_number)
        if not settings.NOTIFICATIONS_FAIL_SILENTLY:
            raise
        return False


def send_whatsapp_order_notifications(order):
    """
    Sends an instant WhatsApp order receipt to the customer's phone
    number, and a separate WhatsApp alert to the merchant.
    Returns (customer_sent: bool, merchant_sent: bool).
    """
    client = _get_twilio_client()
    if client is None:
        return False, False

    item_lines = '\n'.join(
        f'• {item.quantity} x {item.product_name} — Rs {item.line_total}'
        for item in order.items.all()
    )

    customer_body = (
        f'Hi {order.customer_name}, thanks for shopping with SK Mart! 🐝\n\n'
        f'Order #{order.pk} confirmed:\n{item_lines}\n\n'
        f'Total: Rs {order.order_total}\n'
        f'We will text you again once it ships. Track anytime at SK Mart > Track Order.'
    )
    merchant_body = (
        f'🔔 New SK Mart order #{order.pk}\n'
        f'Customer: {order.customer_name} ({order.customer_phone})\n'
        f'{item_lines}\n\n'
        f'Total: Rs {order.order_total}'
    )

    customer_sent = _send_whatsapp_message(client, order.customer_phone, customer_body)
    merchant_sent = _send_whatsapp_message(client, settings.MERCHANT_WHATSAPP_NUMBER, merchant_body)

    if customer_sent:
        logger.info('WhatsApp receipt sent to customer for order #%s', order.pk)
    if merchant_sent:
        logger.info('WhatsApp alert sent to merchant for order #%s', order.pk)

    return customer_sent, merchant_sent


# ----------------------------------------------------------------------
# Single entry point called from views.checkout()
# ----------------------------------------------------------------------
def _notify_new_order_sync(order):
    """
    The actual work: fires all checkout notification triggers for a
    freshly placed order (customer email, merchant email, WhatsApp).
    Runs on a background thread — see notify_new_order() below.
    """
    customer_email_sent = send_customer_confirmation_email(order)
    merchant_email_sent = send_merchant_alert_email(order)
    whatsapp_customer_sent, whatsapp_merchant_sent = send_whatsapp_order_notifications(order)

    order.customer_notified = customer_email_sent or whatsapp_customer_sent
    order.merchant_notified = merchant_email_sent or whatsapp_merchant_sent
    order.save(update_fields=['customer_notified', 'merchant_notified'])

    return {
        'customer_email_sent': customer_email_sent,
        'merchant_email_sent': merchant_email_sent,
        'whatsapp_customer_sent': whatsapp_customer_sent,
        'whatsapp_merchant_sent': whatsapp_merchant_sent,
    }


def notify_new_order(order):
    """
    Call this once, right after the Order + OrderItems are saved.

    Runs email + WhatsApp sending on a background thread so a slow or
    blocked SMTP/Twilio connection can NEVER hang or crash the
    customer's checkout request — the order is already saved in the
    database at this point, so the customer should always get their
    "order placed" page regardless of whether the notification side
    succeeds. (EMAIL_TIMEOUT in settings.py caps how long the SMTP
    connection attempt itself can hang.)
    """
    thread = threading.Thread(
        target=_notify_new_order_sync,
        args=(order,),
        daemon=True,
    )
    thread.start()
