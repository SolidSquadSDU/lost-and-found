from uuid import uuid4

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from items.models import Item
from notifications.models import NotificationOutbox

from .events import ClaimApproved
from .models import Claim
from .publishers import publish_claim_approved
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


@transaction.atomic
def approve_claim(claim):
    # State pattern: delegate approve to the current claim state
    claim = get_claim_state(claim).approve(claim)
    event = ClaimApproved(
        event_id=uuid4(),
        occurred_at=timezone.now(),
        claim_id=claim.pk,
        item_id=claim.item_id,
        claimant_id=claim.claimant_id,
        reporter_id=claim.item.reporter_id,
    )
    # Consumers see committed approval data; a rollback discards this callback.
    transaction.on_commit(lambda: publish_claim_approved(event))
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
