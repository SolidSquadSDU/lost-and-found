from django.db import models

# Create your models here.

class NotificationOutbox(models.Model):
    class EventType(models.TextChoices):
        CLAIM_CREATED = "CLAIM_CREATED", "Claim created"
        CLAIM_APPROVED = "CLAIM_APPROVED", "Claim approved"
        CLAIM_REJECTED = "CLAIM_REJECTED", "Claim rejected"

    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        SENT = "SENT", "Sent"
        FAILED = "FAILED", "Failed"

    claim = models.ForeignKey(
        'claims.Claim',
        on_delete=models.PROTECT,
        related_name="notifications"
    )

    event_type = models.CharField(
        max_length=20,
        choices=EventType.choices,
        default=EventType.CLAIM_CREATED
    )

    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.PENDING
    )

    created_at = models.DateTimeField(auto_now_add=True)

    processed_at = models.DateTimeField(
        null=True,
        blank=True
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["claim", "event_type"],
                name="unique_notification_per_claim_event"
            )
        ]

    def __str__(self):
        return f"{self.event_type} for Claim #{self.claim_id}"