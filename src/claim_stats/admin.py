from django.contrib import admin

from .models import ApprovedClaimsDailyStatistic, ProcessedEvent


@admin.register(ApprovedClaimsDailyStatistic)
class ApprovedClaimsDailyStatisticAdmin(admin.ModelAdmin):
    list_display = ("date", "approved_count")
    ordering = ("-date",)


@admin.register(ProcessedEvent)
class ProcessedEventAdmin(admin.ModelAdmin):
    list_display = ("consumer_name", "event_id", "processed_at")
    list_filter = ("consumer_name",)
