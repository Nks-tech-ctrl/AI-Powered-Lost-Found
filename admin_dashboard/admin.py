from django.contrib import admin
from .models import AuditLog, EmailDelivery


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ('timestamp', 'actor', 'action_type', 'target_model', 'target_object_id', 'short_reason')
    list_filter = ('action_type', 'target_model', 'timestamp')
    search_fields = ('actor__username', 'target_model', 'target_object_id', 'target_repr', 'reason')
    readonly_fields = ('actor', 'action_type', 'target_model', 'target_object_id', 'target_repr', 'previous_state', 'new_state', 'reason', 'ip_address', 'timestamp')

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def short_reason(self, obj):
        return (obj.reason[:60] + '...') if len(obj.reason) > 60 else obj.reason
    short_reason.short_description = 'Reason'


@admin.register(EmailDelivery)
class EmailDeliveryAdmin(admin.ModelAdmin):
    list_display = ('created_at', 'recipient_email', 'event_type', 'subject', 'status', 'attempts', 'sent_at')
    list_filter = ('status', 'event_type', 'created_at')
    search_fields = ('recipient_email', 'subject', 'error_message')
    readonly_fields = ('created_at', 'sent_at')
