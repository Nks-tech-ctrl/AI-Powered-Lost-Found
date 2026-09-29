from django.contrib import admin
from .models import Claim


@admin.register(Claim)
class ClaimAdmin(admin.ModelAdmin):
    list_display = (
        'item',
        'claimant',
        'status',
        'created_at',
        'reviewed_by',
        'reviewed_at',
    )
    list_filter = (
        'status',
        'created_at',
    )
    search_fields = (
        'item__title',
        'claimant__username',
        'claimant__email',
    )
    readonly_fields = (
        'created_at',
        'updated_at',
        'reviewed_at',
    )
    fieldsets = (
        ('Claim Details', {
            'fields': ('item', 'claimant', 'status', 'reason', 'verification_answer')
        }),
        ('Review Outcome', {
            'fields': ('reviewed_by', 'reviewed_at', 'reviewer_note')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )
