"""Shared in-process publication for every ClaimApproved consumer."""

from django.dispatch import Signal

from .events import ClaimApproved


claim_approved = Signal()


def publish_claim_approved(event: ClaimApproved):
    """Notify all subscribers; Django logs errors without stopping other receivers.

    Delivery is synchronous and has no automatic retries. For a manual retry,
    publish the same event again, preserving its event_id.
    """
    return claim_approved.send_robust(sender=ClaimApproved, event=event)
