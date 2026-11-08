from django.core.exceptions import ValidationError

from items.models import Item
from notifications.models import NotificationOutbox

from .models import Claim
from .states import get_claim_state


def create_claim(*, item, claimant, reason):
    if item.status != Item.Status.AVAILABLE:
        raise ValidationError("Only available items can be claimed.")
    if item.reporter_id == claimant.id:
        raise ValidationError("Reporter cannot claim their own item.")

    claim = Claim.objects.create(
        item=item,
        claimant=claimant,
        reason=reason,
        status=Claim.Status.PENDING,
    )
    NotificationOutbox.objects.create(
        claim=claim,
        event_type=NotificationOutbox.EventType.CLAIM_CREATED,
        status=NotificationOutbox.Status.PENDING,
    )
    return claim


def approve_claim(claim):
    # State pattern: delegate approve to the current claim state
    claim = get_claim_state(claim).approve(claim)
    NotificationOutbox.objects.create(
        claim=claim,
        event_type=NotificationOutbox.EventType.CLAIM_APPROVED,
        status=NotificationOutbox.Status.PENDING,
    )
    return claim


def reject_claim(claim):
    # State pattern: delegate reject to the current claim state
    claim = get_claim_state(claim).reject(claim)
    NotificationOutbox.objects.create(
        claim=claim,
        event_type=NotificationOutbox.EventType.CLAIM_REJECTED,
        status=NotificationOutbox.Status.PENDING,
    )
    return claim
