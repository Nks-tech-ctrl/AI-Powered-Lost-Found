from django.db import models
from django.contrib.auth.models import User
from items.models import Item


class Claim(models.Model):
    """
    Represents an ownership claim submitted by an authenticated user for a FOUND item report.
    """

    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        APPROVED = "APPROVED", "Approved"
        REJECTED = "REJECTED", "Rejected"
        CANCELLED = "CANCELLED", "Cancelled"

    item = models.ForeignKey(
        Item,
        on_delete=models.CASCADE,
        related_name="claims"
    )

    claimant = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="claims"
    )

    reason = models.TextField(
        max_length=2000
    )

    verification_answer = models.TextField(
        max_length=2000,
        blank=True
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING
    )

    reviewed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reviewed_claims"
    )

    reviewer_note = models.TextField(
        max_length=2000,
        blank=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    reviewed_at = models.DateTimeField(
        null=True,
        blank=True
    )

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["item"]),
            models.Index(fields=["claimant"]),
            models.Index(fields=["status"]),
            models.Index(fields=["created_at"]),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["claimant", "item"],
                condition=models.Q(status="PENDING"),
                name="unique_pending_claim_per_user_item"
            )
        ]

    def __str__(self):
        return f"Claim by {self.claimant.username} for {self.item.title}"
