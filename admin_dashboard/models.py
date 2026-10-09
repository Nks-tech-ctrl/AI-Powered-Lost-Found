from django.db import models
from django.contrib.auth.models import User


class AuditLog(models.Model):
    """
    Append-only audit trail for sensitive administrative operations,
    user account state changes, item moderation, and claim interventions.
    """

    class ActionType(models.TextChoices):
        USER_DEACTIVATED = 'USER_DEACTIVATED', 'User Deactivated'
        USER_ACTIVATED = 'USER_ACTIVATED', 'User Activated'
        USER_UPDATED = 'USER_UPDATED', 'User Updated'
        ITEM_MODERATED = 'ITEM_MODERATED', 'Item Moderated'
        ITEM_HIDDEN = 'ITEM_HIDDEN', 'Item Hidden'
        ITEM_RESTORED = 'ITEM_RESTORED', 'Item Restored'
        ITEM_CLOSED = 'ITEM_CLOSED', 'Item Closed'
        CLAIM_APPROVED_ADMIN = 'CLAIM_APPROVED_ADMIN', 'Claim Approved by Admin'
        CLAIM_REJECTED_ADMIN = 'CLAIM_REJECTED_ADMIN', 'Claim Rejected by Admin'
        CLAIM_INTERVENTION = 'CLAIM_INTERVENTION', 'Claim Administrative Intervention'
        SETTINGS_UPDATED = 'SETTINGS_UPDATED', 'Settings Updated'
        PERMISSION_CHANGED = 'PERMISSION_CHANGED', 'Permission Changed'

    actor = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='admin_audit_logs'
    )
    action_type = models.CharField(
        max_length=50,
        choices=ActionType.choices,
        db_index=True
    )
    target_model = models.CharField(
        max_length=50
    )
    target_object_id = models.CharField(
        max_length=50,
        blank=True
    )
    target_repr = models.CharField(
        max_length=255,
        blank=True
    )
    previous_state = models.JSONField(
        null=True,
        blank=True
    )
    new_state = models.JSONField(
        null=True,
        blank=True
    )
    reason = models.TextField(
        blank=True
    )
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True
    )
    timestamp = models.DateTimeField(
        auto_now_add=True,
        db_index=True
    )

    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['action_type', 'timestamp']),
            models.Index(fields=['target_model', 'target_object_id']),
            models.Index(fields=['actor', 'timestamp']),
        ]
        permissions = [
            ('view_dashboard_stats', 'Can view admin dashboard statistics'),
            ('manage_users', 'Can manage users in admin dashboard'),
            ('moderate_items', 'Can moderate items in admin dashboard'),
            ('manage_claims', 'Can manage claims in admin dashboard'),
            ('view_audit_logs', 'Can view audit logs'),
            ('view_email_logs', 'Can view email delivery logs'),
            ('manage_settings', 'Can manage platform settings'),
        ]

    def __str__(self):
        actor_name = self.actor.username if self.actor else "System"
        return f"[{self.timestamp.strftime('%Y-%m-%d %H:%M')}] {actor_name} -> {self.action_type} on {self.target_model}:{self.target_object_id}"


class EmailDelivery(models.Model):
    """
    Tracks outgoing email notifications, their dispatch status,
    delivery attempts, and error details without storing sensitive payload secrets.
    """

    class DeliveryStatus(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        SENT = 'SENT', 'Sent'
        FAILED = 'FAILED', 'Failed'

    class EventType(models.TextChoices):
        CLAIM_SUBMITTED = 'CLAIM_SUBMITTED', 'Claim Submitted'
        CLAIM_APPROVED = 'CLAIM_APPROVED', 'Claim Approved'
        CLAIM_REJECTED = 'CLAIM_REJECTED', 'Claim Rejected'
        CLAIM_CANCELLED = 'CLAIM_CANCELLED', 'Claim Cancelled'
        CLAIM_SUPERSEDED = 'CLAIM_SUPERSEDED', 'Claim Superseded'
        REPORT_STATUS_CHANGED = 'REPORT_STATUS_CHANGED', 'Report Status Changed'
        REPORT_MODERATED = 'REPORT_MODERATED', 'Report Moderated'
        ACCOUNT_STATUS_CHANGED = 'ACCOUNT_STATUS_CHANGED', 'Account Status Changed'
        GENERAL_NOTIFICATION = 'GENERAL_NOTIFICATION', 'General Notification'

    recipient_email = models.EmailField(
        db_index=True
    )
    recipient_user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='email_deliveries'
    )
    subject = models.CharField(
        max_length=255
    )
    event_type = models.CharField(
        max_length=50,
        choices=EventType.choices,
        db_index=True
    )
    status = models.CharField(
        max_length=20,
        choices=DeliveryStatus.choices,
        default=DeliveryStatus.PENDING,
        db_index=True
    )
    attempts = models.PositiveIntegerField(
        default=1
    )
    error_message = models.TextField(
        blank=True
    )
    notification = models.ForeignKey(
        'notifications.Notification',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='email_deliveries'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True
    )
    sent_at = models.DateTimeField(
        null=True,
        blank=True
    )

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'created_at']),
            models.Index(fields=['event_type', 'status']),
            models.Index(fields=['recipient_email', 'status']),
        ]

    def __str__(self):
        return f"Email {self.event_type} to {self.recipient_email} [{self.status}]"
