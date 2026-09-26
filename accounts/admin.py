from django.contrib import admin
from .models import UserProfile


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'phone', 'location', 'created_at', 'updated_at')
    search_fields = ('user__username', 'user__email', 'user__first_name', 'user__last_name', 'phone', 'location')
    list_filter = ('match_notifications', 'claim_notifications', 'report_notifications', 'community_notifications', 'created_at')
    readonly_fields = ('created_at', 'updated_at')
