from claims.events import ClaimApproved

from .models import AuditRecord


class ApprovalAuditConsumer:
    @staticmethod
    def handle(*, event: ClaimApproved, **kwargs):
        """Save an audit record for an approved claim, once per event.

        `event_id` is unique in the database and get_or_create() handles
        concurrent delivery, so redelivering the same event returns the
        existing record instead of writing a second one.
        """
        record, _ = AuditRecord.objects.get_or_create(
            event_id=event.event_id,
            defaults={
                "action": AuditRecord.Action.CLAIM_APPROVED,
                "claim_id": event.claim_id,
                "item_id": event.item_id,
                "claimant_id": event.claimant_id,
                "reporter_id": event.reporter_id,
                "occurred_at": event.occurred_at,
            },
        )
        return record
