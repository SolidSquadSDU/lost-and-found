from unittest.mock import patch
from uuid import uuid4

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from claims.events import ClaimApproved
from claims.models import Claim
from claims.publishers import publish_claim_approved
from claims.services import approve_claim, create_claim, reject_claim
from items.services import report_item
from notifications.models import NotificationOutbox

User = get_user_model()


class NotificationOutboxTests(TestCase):

    def setUp(self):
        reporter = User.objects.create_user(username="reporter", password="pass")
        claimant = User.objects.create_user(username="claimant", password="pass")
        item = report_item(
            reporter=reporter,
            title="Wallet",
            description="Brown wallet",
            found_location="Hall",
        )
        self.claim = create_claim(item=item, claimant=claimant, reason="Mine")

    def has_event(self, event_type):
        return NotificationOutbox.objects.filter(
            claim=self.claim, event_type=event_type
        ).exists()

    def test_create_claim_writes_claim_created(self):
        self.assertTrue(self.has_event(NotificationOutbox.EventType.CLAIM_CREATED))

    def test_approve_claim_writes_claim_approved(self):
        # The consumer runs after commit, so run the on_commit callbacks.
        with self.captureOnCommitCallbacks(execute=True):
            approve_claim(self.claim)
        self.assertTrue(self.has_event(NotificationOutbox.EventType.CLAIM_APPROVED))

    def test_reject_claim_writes_claim_rejected(self):
        reject_claim(self.claim)
        self.assertTrue(self.has_event(NotificationOutbox.EventType.CLAIM_REJECTED))


class ApprovalNotificationConsumerTests(TestCase):

    def setUp(self):
        reporter = User.objects.create_user(username="reporter", password="pass")
        claimant = User.objects.create_user(username="claimant", password="pass")
        item = report_item(
            reporter=reporter,
            title="Wallet",
            description="Brown wallet",
            found_location="Hall",
        )
        self.claim = create_claim(item=item, claimant=claimant, reason="Mine")

    def approved_rows(self):
        return NotificationOutbox.objects.filter(
            claim=self.claim,
            event_type=NotificationOutbox.EventType.CLAIM_APPROVED,
        )

    def test_successful_reaction(self):
        with patch(
            "claims.services.publish_claim_approved",
            wraps=publish_claim_approved,
        ) as publisher:
            with self.captureOnCommitCallbacks(execute=True):
                approve_claim(self.claim)

        # 1. main operation succeeded
        self.claim.refresh_from_db()
        self.assertEqual(self.claim.status, Claim.Status.APPROVED)
        # 2. event was published
        publisher.assert_called_once()
        self.assertEqual(publisher.call_args.args[0].claim_id, self.claim.pk)
        # 3. consumer created a pending notification
        notification = self.approved_rows().get()
        self.assertEqual(notification.status, NotificationOutbox.Status.PENDING)

    def test_duplicate_delivery_creates_one_notification(self):
        event = ClaimApproved(
            event_id=uuid4(),
            occurred_at=timezone.now(),
            claim_id=self.claim.pk,
            item_id=self.claim.item_id,
            claimant_id=self.claim.claimant_id,
            reporter_id=self.claim.item.reporter_id,
        )

        publish_claim_approved(event)
        publish_claim_approved(event)

        self.assertEqual(self.approved_rows().count(), 1)
