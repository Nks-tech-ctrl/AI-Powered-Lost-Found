from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class Notification(models.Model):
    """
    Database-backed in-app notification model for FindBack events,
    such as ownership claim submissions, approvals, rejections, cancellations,
    and superseded status updates.
    """

    class NotificationType(models.TextChoices):
        CLAIM_SUBMITTED = 'CLAIM_SUBMITTED', 'Claim Submitted'
        CLAIM_APPROVED = 'CLAIM_APPROVED', 'Claim Approved'
        CLAIM_REJECTED = 'CLAIM_REJECTED', 'Claim Rejected'
        CLAIM_CANCELLED = 'CLAIM_CANCELLED', 'Claim Cancelled'
        CLAIM_SUPERSEDED = 'CLAIM_SUPERSEDED', 'Claim Superseded'
        ITEM_STATUS_CHANGED = 'ITEM_STATUS_CHANGED', 'Item Status Changed'
        MODERATION_ACTION = 'MODERATION_ACTION', 'Moderation Action'
        ACCOUNT_STATUS_CHANGED = 'ACCOUNT_STATUS_CHANGED', 'Account Status Changed'
        ADMIN_ALERT = 'ADMIN_ALERT', 'Admin Alert'

    recipient = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='notifications'
    )

    notification_type = models.CharField(
        max_length=30,
        choices=NotificationType.choices
    )

    title = models.CharField(
        max_length=200
    )

    message = models.TextField(
        max_length=2000
    )

    is_read = models.BooleanField(
        default=False
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    read_at = models.DateTimeField(
        null=True,
        blank=True
    )

    item = models.ForeignKey(
        'items.Item',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='notifications'
    )

    claim = models.ForeignKey(
        'claims.Claim',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='notifications'
    )

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['recipient', 'is_read']),
            models.Index(fields=['recipient', 'created_at']),
            models.Index(fields=['notification_type']),
        ]

    def mark_as_read(self):
        """Marks the notification as read with a timestamp."""
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save(update_fields=['is_read', 'read_at'])

    def __str__(self):
        return f"Notification for {self.recipient.username}: {self.title}"
