from django.db import models
from django.conf import settings
# Create your models here.

class Claim(models.Model):
    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        APPROVED = "APPROVED", "Approved"
        REJECTED = "REJECTED", "Rejected"

    item = models.ForeignKey(
        "items.Item",
        on_delete=models.PROTECT,
        related_name="claims"
    )

    claimant = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="claims"
    )

    reason = models.TextField()

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields = ["item", "claimant"],
                name = "unique_claim_per_user_item"
            )
        ]

    def __str__(self):
        return f"Claim #{self.id} for {self.item.title}"