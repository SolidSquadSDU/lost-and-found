from django.contrib import admin
from .models import Claim, HandoverTask
# Register your models here.

@admin.register(Claim)
class ClaimAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "item",
        "claimant",
        "status",
        "created_at"
    )

    list_filter = ("status", "created_at")
    search_fields = ("item__title", "claimant__username")


@admin.register(HandoverTask)
class HandoverTaskAdmin(admin.ModelAdmin):
    list_display = ("id", "claim", "status", "approved_at", "created_at")
    list_filter = ("status", "created_at")
    search_fields = ("claim__item__title", "claim__claimant__username")
    readonly_fields = ("claim", "source_event_id", "approved_at", "created_at")

    def has_add_permission(self, request):
        # Tasks are created by ClaimApproved, with their event metadata intact.
        return False
