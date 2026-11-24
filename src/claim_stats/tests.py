from unittest.mock import patch
from uuid import uuid4

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from claims.events import ClaimApproved
from claims.models import Claim
from claims.publishers import publish_claim_approved
from claims.services import approve_claim, create_claim
from items.models import Item
from items.services import report_item

from .consumers import ApprovedClaimsStatisticsConsumer
from .models import ApprovedClaimsDailyStatistic, ProcessedEvent


class ApprovedClaimsStatisticsConsumerTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.reporter = User.objects.create_user(username="stats-reporter")
        self.claimant = User.objects.create_user(username="stats-claimant")
        self.item = report_item(
            reporter=self.reporter,
            title="Brown wallet",
            description="Leather wallet with a bus card",
            found_location="Canteen",
        )
        self.claim = create_claim(
            item=self.item,
            claimant=self.claimant,
            reason="My bus card is inside.",
        )

    def test_approval_publishes_event_and_updates_daily_statistic(self):
        with patch(
            "claims.services.publish_claim_approved", wraps=publish_claim_approved
        ) as publisher:
            with self.captureOnCommitCallbacks(execute=True):
                approve_claim(self.claim)

        # 1. The main operation succeeded.
        self.claim.refresh_from_db()
        self.item.refresh_from_db()
        self.assertEqual(self.claim.status, Claim.Status.APPROVED)
        self.assertEqual(self.item.status, Item.Status.CLAIMED)

        # 2. The event was published.
        publisher.assert_called_once()
        event = publisher.call_args.args[0]
        self.assertIsInstance(event, ClaimApproved)
        self.assertEqual(event.claim_id, self.claim.pk)

        # 3. The consumer updated the stored daily count.
        stat = ApprovedClaimsDailyStatistic.objects.get(
            date=timezone.localdate(event.occurred_at)
        )
        self.assertEqual(stat.approved_count, 1)
        self.assertTrue(
            ProcessedEvent.objects.filter(
                consumer_name=ApprovedClaimsStatisticsConsumer.NAME,
                event_id=event.event_id,
            ).exists()
        )

    def test_same_event_published_twice_is_counted_once(self):
        event = ClaimApproved(
            event_id=uuid4(),
            occurred_at=timezone.now(),
            claim_id=self.claim.pk,
            item_id=self.item.pk,
            claimant_id=self.claimant.pk,
            reporter_id=self.reporter.pk,
        )

        publish_claim_approved(event)
        publish_claim_approved(event)

        stat = ApprovedClaimsDailyStatistic.objects.get(
            date=timezone.localdate(event.occurred_at)
        )
        self.assertEqual(stat.approved_count, 1)
        self.assertEqual(
            ProcessedEvent.objects.filter(
                consumer_name=ApprovedClaimsStatisticsConsumer.NAME,
                event_id=event.event_id,
            ).count(),
            1,
        )
