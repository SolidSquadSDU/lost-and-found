from django.db import models


class ApprovedClaimsDailyStatistic(models.Model):
    """Number of claims approved on each calendar day."""

    date = models.DateField(unique=True)
    approved_count = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"{self.date}: {self.approved_count} approved"


class ProcessedEvent(models.Model):
    """Marks an event as handled by one consumer (duplicate-delivery protection)."""

    consumer_name = models.CharField(max_length=100)
    event_id = models.UUIDField()
    processed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["consumer_name", "event_id"],
                name="unique_processed_event_per_consumer",
            )
        ]

    def __str__(self):
        return f"{self.consumer_name} processed {self.event_id}"
