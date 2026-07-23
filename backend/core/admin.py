from django.contrib import admin

from .models import AuditLog


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    """Read-only view of the audit trail. Never hand-edit these rows."""

    list_display = ['created_at', 'actor', 'action', 'resource_type', 'resource_id', 'ip_address']
    list_filter = ['action', 'resource_type', 'created_at']
    search_fields = ['actor__username', 'resource_id', 'user_agent']
    readonly_fields = [f.name for f in AuditLog._meta.fields]
    date_hierarchy = 'created_at'

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
