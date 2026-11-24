from .events import ClaimApproved
from .models import HandoverTask


class HandoverTaskConsumer:
    @staticmethod
    def handle(*, event: ClaimApproved, **kwargs):
        """Arrange collection once, even when approval is delivered again.

        The unique claim and source_event_id columns enforce this in the
        database. get_or_create() also handles concurrent duplicate delivery.
        The claim links the task to its item, claimant, and reporter.
        """
        task, _ = HandoverTask.objects.get_or_create(
            claim_id=event.claim_id,
            defaults={
                "source_event_id": event.event_id,
                "approved_at": event.occurred_at,
                "status": HandoverTask.Status.PENDING,
            },
        )
        return task
