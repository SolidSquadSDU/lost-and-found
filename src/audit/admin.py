from django.contrib import admin

from .models import AuditRecord


@admin.register(AuditRecord)
class AuditRecordAdmin(admin.ModelAdmin):
    list_display = ("action", "claim_id", "item_id", "occurred_at", "event_id")
    readonly_fields = [f.name for f in AuditRecord._meta.fields]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
