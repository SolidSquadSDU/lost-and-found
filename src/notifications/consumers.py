from claims.events import ClaimApproved

from .models import NotificationOutbox


class ApprovalNotificationConsumer:
    @staticmethod
    def handle(*, event: ClaimApproved, **kwargs):
        """Queue the approval notification once, even if the event is redelivered.

        The unique (claim, event_type) constraint plus get_or_create() makes
        duplicate delivery return the existing row.
        """
        notification, _ = NotificationOutbox.objects.get_or_create(
            claim_id=event.claim_id,
            event_type=NotificationOutbox.EventType.CLAIM_APPROVED,
            defaults={"status": NotificationOutbox.Status.PENDING},
        )
        return notification
