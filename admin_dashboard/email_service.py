import logging
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils import timezone
from django.utils.html import strip_tags

from .models import EmailDelivery

logger = logging.getLogger(__name__)


TEMPLATE_MAPPING = {
    EmailDelivery.EventType.CLAIM_SUBMITTED: 'emails/claim-submitted.html',
    EmailDelivery.EventType.CLAIM_APPROVED: 'emails/claim-approved.html',
    EmailDelivery.EventType.CLAIM_REJECTED: 'emails/claim-rejected.html',
    EmailDelivery.EventType.CLAIM_CANCELLED: 'emails/notification.html',
    EmailDelivery.EventType.CLAIM_SUPERSEDED: 'emails/notification.html',
    EmailDelivery.EventType.REPORT_STATUS_CHANGED: 'emails/report-status-changed.html',
    EmailDelivery.EventType.REPORT_MODERATED: 'emails/report-status-changed.html',
    EmailDelivery.EventType.ACCOUNT_STATUS_CHANGED: 'emails/account-status-changed.html',
    EmailDelivery.EventType.GENERAL_NOTIFICATION: 'emails/notification.html',
}

SUBJECT_DEFAULTS = {
    EmailDelivery.EventType.CLAIM_SUBMITTED: '[FindBack] New Ownership Claim Submitted',
    EmailDelivery.EventType.CLAIM_APPROVED: '[FindBack] Your Ownership Claim Has Been Approved!',
    EmailDelivery.EventType.CLAIM_REJECTED: '[FindBack] Update on Your Ownership Claim',
    EmailDelivery.EventType.CLAIM_CANCELLED: '[FindBack] A Claim on Your Item Was Cancelled',
    EmailDelivery.EventType.CLAIM_SUPERSEDED: '[FindBack] Notice Regarding Your Claim',
    EmailDelivery.EventType.REPORT_STATUS_CHANGED: '[FindBack] Status Update on Your Report',
    EmailDelivery.EventType.REPORT_MODERATED: '[FindBack] Important Notice Regarding Your Report',
    EmailDelivery.EventType.ACCOUNT_STATUS_CHANGED: '[FindBack] Security Notice: Your Account Status Has Changed',
    EmailDelivery.EventType.GENERAL_NOTIFICATION: '[FindBack] Notification from FindBack',
}


def user_accepts_email_for_event(user, event_type):
    """
    Checks user's notification preferences from their UserProfile.
    Essential security/account notifications are always permitted.
    """
    if not user or not hasattr(user, 'profile'):
        return True
    
    # Account status notifications are essential security notices
    if event_type == EmailDelivery.EventType.ACCOUNT_STATUS_CHANGED:
        return True
    
    profile = user.profile
    if event_type in [
        EmailDelivery.EventType.CLAIM_SUBMITTED,
        EmailDelivery.EventType.CLAIM_APPROVED,
        EmailDelivery.EventType.CLAIM_REJECTED,
        EmailDelivery.EventType.CLAIM_CANCELLED,
        EmailDelivery.EventType.CLAIM_SUPERSEDED,
    ]:
        return getattr(profile, 'claim_notifications', True)

    if event_type in [
        EmailDelivery.EventType.REPORT_STATUS_CHANGED,
        EmailDelivery.EventType.REPORT_MODERATED,
    ]:
        return getattr(profile, 'report_notifications', True)

    return True


def send_event_email(recipient_user, event_type, context=None, subject=None, notification=None):
    """
    Sends an HTML & plain-text event email and tracks its delivery in EmailDelivery.
    Never fails the calling transaction if email sending encounters an error.

    Args:
        recipient_user (User): The recipient user model instance.
        event_type (str): Key from EmailDelivery.EventType.
        context (dict, optional): Context dictionary for the email templates.
        subject (str, optional): Custom email subject override.
        notification (Notification, optional): Linked in-app notification.

    Returns:
        EmailDelivery: The tracked delivery record.
    """
    if not recipient_user or not recipient_user.email:
        logger.info(f"Skipping email dispatch for user {recipient_user}: No valid email address.")
        return None

    if not user_accepts_email_for_event(recipient_user, event_type):
        logger.info(f"User {recipient_user.username} opted out of email notifications for {event_type}.")
        return None

    context = context.copy() if context else {}
    context.setdefault('user', recipient_user)
    context.setdefault('site_url', getattr(settings, 'SITE_URL', 'http://127.0.0.1:8000'))
    context.setdefault('event_type', event_type)

    email_subject = subject or SUBJECT_DEFAULTS.get(event_type, '[FindBack] Update on Your Account')
    template_name = TEMPLATE_MAPPING.get(event_type, 'emails/notification.html')

    # Create delivery record in PENDING status
    delivery = EmailDelivery.objects.create(
        recipient_email=recipient_user.email,
        recipient_user=recipient_user,
        subject=email_subject,
        event_type=event_type,
        status=EmailDelivery.DeliveryStatus.PENDING,
        notification=notification,
    )

    try:
        html_content = render_to_string(template_name, context)
        plain_content = strip_tags(html_content)

        from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'FindBack <noreply@findback.local>')
        msg = EmailMultiAlternatives(
            subject=email_subject,
            body=plain_content,
            from_email=from_email,
            to=[recipient_user.email]
        )
        msg.attach_alternative(html_content, "text/html")
        msg.send(fail_silently=False)

        delivery.status = EmailDelivery.DeliveryStatus.SENT
        delivery.sent_at = timezone.now()
        delivery.save(update_fields=['status', 'sent_at'])
        logger.info(f"Successfully dispatched email {delivery.id} to {recipient_user.email}")
    except Exception as e:
        error_msg = str(e)
        logger.warning(f"Failed to dispatch email {delivery.id} to {recipient_user.email}: {error_msg}")
        delivery.status = EmailDelivery.DeliveryStatus.FAILED
        delivery.error_message = error_msg[:1000]
        delivery.save(update_fields=['status', 'error_message'])

    return delivery
