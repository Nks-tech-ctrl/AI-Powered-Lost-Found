import os
from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.utils import timezone


def validate_not_future_date(value):
    """
    Validates that the date_occurred is not in the future.
    Uses timezone-aware date comparisons.
    """
    if value and value > timezone.now().date():
        raise ValidationError('The lost/found date cannot be in the future.')


class Item(models.Model):
    """
    Unified Lost and Found item report database model.
    Serves as the single core entity for both LOST and FOUND items.
    """

    class ItemType(models.TextChoices):
        LOST = 'LOST', 'Lost'
        FOUND = 'FOUND', 'Found'

    class ItemStatus(models.TextChoices):
        ACTIVE = 'ACTIVE', 'Active'
        MATCHED = 'MATCHED', 'Potential Match'
        CLAIMED = 'CLAIMED', 'Claimed'
        RETURNED = 'RETURNED', 'Returned'
        CLOSED = 'CLOSED', 'Closed'

    class ItemCategory(models.TextChoices):
        ELECTRONICS = 'ELECTRONICS', 'Electronics'
        MOBILE = 'MOBILE', 'Mobile Phone'
        LAPTOP = 'LAPTOP', 'Laptop'
        TABLET = 'TABLET', 'Tablet'
        WATCH = 'WATCH', 'Watch'
        WALLET = 'WALLET', 'Wallet'
        BAG = 'BAG', 'Bag'
        KEYS = 'KEYS', 'Keys'
        DOCUMENT = 'DOCUMENT', 'Documents'
        ID_CARD = 'ID_CARD', 'ID Card'
        JEWELRY = 'JEWELRY', 'Jewelry'
        CLOTHING = 'CLOTHING', 'Clothing'
        ACCESSORY = 'ACCESSORY', 'Accessories'
        BOOK = 'BOOK', 'Books'
        STATIONERY = 'STATIONERY', 'Stationery'
        VEHICLE = 'VEHICLE', 'Vehicle'
        OTHER = 'OTHER', 'Other'

    # Ownership: Every report belongs to the authenticated user who submitted it
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='items'
    )

    # Core classifications
    item_type = models.CharField(
        max_length=10,
        choices=ItemType.choices
    )
    status = models.CharField(
        max_length=20,
        choices=ItemStatus.choices,
        default=ItemStatus.ACTIVE
    )
    category = models.CharField(
        max_length=30,
        choices=ItemCategory.choices
    )

    # Basic item information
    title = models.CharField(
        max_length=150
    )
    description = models.TextField(
        max_length=2000
    )
    brand = models.CharField(
        max_length=100,
        blank=True
    )
    color = models.CharField(
        max_length=50,
        blank=True
    )

    # Location (text representation for development; maps/geolocation in future)
    location = models.CharField(
        max_length=255
    )

    # Incident date & time (distinguished from report creation timestamp)
    date_occurred = models.DateField(
        validators=[validate_not_future_date]
    )
    time_occurred = models.TimeField(
        null=True,
        blank=True
    )

    # Item media
    image = models.ImageField(
        upload_to='items/',
        blank=True,
        null=True
    )

    # Private ownership clues for claim verification (never exposed publicly)
    identification_details = models.TextField(
        max_length=1000,
        blank=True
    )

    # Audit timestamps
    created_at = models.DateTimeField(
        auto_now_add=True
    )
    updated_at = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['item_type']),
            models.Index(fields=['category']),
            models.Index(fields=['status']),
            models.Index(fields=['location']),
            models.Index(fields=['date_occurred']),
            models.Index(fields=['created_at']),
        ]

    def clean(self):
        super().clean()
        if self.date_occurred and self.date_occurred > timezone.now().date():
            raise ValidationError({
                'date_occurred': 'The lost/found date cannot be in the future.'
            })

    def __str__(self):
        return self.title
