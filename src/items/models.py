from django.db import models
from django.conf import settings
# Create your models here.

class Item(models.Model):

    class Status(models.TextChoices):
        AVAILABLE = "AVAILABLE", "Available"
        CLAIMED = "CLAIMED", "Claimed"
        RETURNED = "RETURNED", "Returned"

    reporter = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="reported_items"
    )

    title = models.CharField(max_length=120)

    description = models.TextField()

    found_location = models.CharField(max_length=200)

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.AVAILABLE
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title