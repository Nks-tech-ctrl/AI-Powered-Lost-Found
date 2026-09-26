from django.db import models
from django.contrib.auth.models import User


class UserProfile(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='profile'
    )
    profile_picture = models.ImageField(
        upload_to='profiles/',
        blank=True,
        null=True
    )
    phone = models.CharField(
        max_length=20,
        blank=True
    )
    location = models.CharField(
        max_length=150,
        blank=True
    )
    bio = models.TextField(
        max_length=500,
        blank=True
    )

    # Notification preferences
    match_notifications = models.BooleanField(default=True)
    claim_notifications = models.BooleanField(default=True)
    report_notifications = models.BooleanField(default=True)
    community_notifications = models.BooleanField(default=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.user.username
