from django.db import IntegrityError, transaction
from django.db.models import F
from django.utils import timezone

from claims.events import ClaimApproved

from .models import ApprovedClaimsDailyStatistic, ProcessedEvent


class ApprovedClaimsStatisticsConsumer:
    """Reacts to ClaimApproved by updating the stored daily count of approved claims."""

    NAME = "ApprovedClaimsStatisticsConsumer"

    @staticmethod
    def handle(*, event: ClaimApproved, **kwargs):
        try:
            with transaction.atomic():
                # Duplicate protection: the processed-event marker and the counter
                # update are written in one transaction. A second delivery of the
                # same event violates the unique (consumer_name, event_id) key, the
                # transaction rolls back, and the counter is not incremented again.
                ProcessedEvent.objects.create(
                    consumer_name=ApprovedClaimsStatisticsConsumer.NAME,
                    event_id=event.event_id,
                )
                day = timezone.localdate(event.occurred_at)
                ApprovedClaimsDailyStatistic.objects.get_or_create(date=day)
                ApprovedClaimsDailyStatistic.objects.filter(date=day).update(
                    approved_count=F("approved_count") + 1
                )
        except IntegrityError:
            return False  # already processed
        return True
