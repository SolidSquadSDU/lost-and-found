from django.db import models


class AuditRecord(models.Model):
    """Append-only trace of a business fact, written by ApprovalAuditConsumer.

    Ids are stored as plain integers (not foreign keys) so the audit trail
    never blocks, or is changed by, later edits to claims, items or users.
    """

    class Action(models.TextChoices):
        CLAIM_APPROVED = "CLAIM_APPROVED", "Claim approved"

    # Duplicate protection: one audit row per event, enforced by the database.
    event_id = models.UUIDField(unique=True, editable=False)
    action = models.CharField(max_length=30, choices=Action.choices)
    claim_id = models.PositiveIntegerField()
    item_id = models.PositiveIntegerField()
    claimant_id = models.PositiveIntegerField()
    reporter_id = models.PositiveIntegerField()
    occurred_at = models.DateTimeField()
    recorded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-occurred_at"]

    def __str__(self):
        return f"{self.action} claim #{self.claim_id} ({self.event_id})"
