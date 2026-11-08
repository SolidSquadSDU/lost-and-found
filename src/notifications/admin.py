from django.contrib import admin
from .models import NotificationOutbox
# Register your models here.

@admin.register(NotificationOutbox)
class NotificationOutboxAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "claim",
        "event_type",
        "status",
        "created_at",
        "processed_at"
    )

    list_filter = ("event_type", "status")
    search_fields = ("claim__item__title",)