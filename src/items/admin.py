from django.contrib import admin
from .models import Item

# Register your models here.
@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "title",
        "reporter",
        "found_location",
        "status",
        "created_at"
    )

    list_filter = ("status", "created_at")
    search_fields = ("title", "description")