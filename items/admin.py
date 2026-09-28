from django.contrib import admin
from .models import Item


@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    """
    Admin management interface for Lost & Found items.
    """
    list_display = (
        'title',
        'user',
        'item_type',
        'category',
        'location',
        'status',
        'date_occurred',
        'created_at',
    )

    list_filter = (
        'item_type',
        'category',
        'status',
        'date_occurred',
        'created_at',
    )

    search_fields = (
        'title',
        'description',
        'location',
        'brand',
        'color',
        'user__username',
        'user__email',
    )

    readonly_fields = ('created_at', 'updated_at')

    fieldsets = (
        ('Basic Information', {
            'fields': (
                'title',
                'user',
                'item_type',
                'category',
                'status',
            )
        }),
        ('Description & Attributes', {
            'fields': (
                'description',
                'brand',
                'color',
            )
        }),
        ('Location & Incident Timing', {
            'fields': (
                'location',
                'date_occurred',
                'time_occurred',
            )
        }),
        ('Media', {
            'fields': (
                'image',
            )
        }),
        ('Ownership Verification (Private / Confidential)', {
            'description': 'Sensitive verification marks only visible to authorized administrators for claim challenges.',
            'fields': (
                'identification_details',
            )
        }),
        ('Timestamps', {
            'classes': ('collapse',),
            'fields': (
                'created_at',
                'updated_at',
            )
        }),
    )
