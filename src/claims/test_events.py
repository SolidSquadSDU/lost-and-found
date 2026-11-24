from unittest.mock import patch
from uuid import UUID, uuid4

from django.contrib.auth import get_user_model
from django.db import transaction
from django.test import TestCase
from django.utils import timezone

from items.models import Item
from items.services import report_item
from notifications.models import NotificationOutbox

from .events import ClaimApproved
from .models import Claim, HandoverTask
from .publishers import claim_approved, publish_claim_approved
from .services import approve_claim, create_claim, reject_claim
from .states import ClaimTransitionError


class ClaimApprovedEventTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.reporter = User.objects.create_user(username="event-reporter")
        self.claimant = User.objects.create_user(username="event-claimant")
        self.item = report_item(
            reporter=self.reporter,
            title="Black backpack",
            description="Blue keychain",
            found_location="Library",
        )
        self.claim = create_claim(
            item=self.item,
            claimant=self.claimant,
            reason="My student ID is inside.",
        )

    def make_event(self):
        return ClaimApproved(
            event_id=uuid4(),
            occurred_at=timezone.now(),
            claim_id=self.claim.pk,
            item_id=self.item.pk,
            claimant_id=self.claimant.pk,
            reporter_id=self.reporter.pk,
        )

    def test_approval_publishes_event_and_creates_handover_task(self):
        before = timezone.now()
        with patch(
            "claims.services.publish_claim_approved", wraps=publish_claim_approved
        ) as publisher:
            # TestCase wraps each test in a transaction, so execute its callbacks.
            with self.captureOnCommitCallbacks(execute=True) as callbacks:
                result = approve_claim(self.claim)
                publisher.assert_not_called()
                self.assertFalse(HandoverTask.objects.exists())

        self.claim.refresh_from_db()
        self.item.refresh_from_db()
        self.assertEqual(result.pk, self.claim.pk)
        self.assertEqual(self.claim.status, Claim.Status.APPROVED)
        self.assertEqual(self.item.status, Item.Status.CLAIMED)
        self.assertEqual(len(callbacks), 1)
        publisher.assert_called_once()
        event = publisher.call_args.args[0]
        self.assertIsInstance(event, ClaimApproved)
        self.assertIsInstance(event.event_id, UUID)
        self.assertTrue(timezone.is_aware(event.occurred_at))
        self.assertGreaterEqual(event.occurred_at, before)
        self.assertLessEqual(event.occurred_at, timezone.now())
        self.assertEqual(event.claim_id, self.claim.pk)
        self.assertEqual(event.item_id, self.item.pk)
        self.assertEqual(event.claimant_id, self.claimant.pk)
        self.assertEqual(event.reporter_id, self.reporter.pk)

        task = HandoverTask.objects.get()
        self.assertEqual(task.claim_id, self.claim.pk)
        self.assertEqual(task.source_event_id, event.event_id)
        self.assertEqual(task.approved_at, event.occurred_at)
        self.assertEqual(task.status, HandoverTask.Status.PENDING)

    def test_duplicate_delivery_creates_only_one_handover_task(self):
        # Redeliver the exact event already published by a real approval.
        with patch(
            "claims.services.publish_claim_approved", wraps=publish_claim_approved
        ) as publisher:
            with self.captureOnCommitCallbacks(execute=True):
                approve_claim(self.claim)
        event = publisher.call_args.args[0]
        task = HandoverTask.objects.get()
        task.status = HandoverTask.Status.COMPLETED
        task.save(update_fields=["status"])

        publish_claim_approved(event)

        self.assertEqual(HandoverTask.objects.count(), 1)
        task.refresh_from_db()
        self.assertEqual(task.source_event_id, event.event_id)
        self.assertEqual(task.status, HandoverTask.Status.COMPLETED)

    def test_rolled_back_approval_does_not_publish(self):
        with patch("claims.services.publish_claim_approved") as publisher:
            with self.captureOnCommitCallbacks(execute=True) as callbacks:
                with self.assertRaisesMessage(RuntimeError, "Cancel transaction"):
                    with transaction.atomic():
                        approve_claim(self.claim)
                        raise RuntimeError("Cancel transaction")

        publisher.assert_not_called()
        self.assertEqual(callbacks, [])
        self.claim.refresh_from_db()
        self.item.refresh_from_db()
        self.assertEqual(self.claim.status, Claim.Status.PENDING)
        self.assertEqual(self.item.status, Item.Status.AVAILABLE)
        self.assertFalse(HandoverTask.objects.exists())
        self.assertFalse(
            NotificationOutbox.objects.filter(
                claim=self.claim,
                event_type=NotificationOutbox.EventType.CLAIM_APPROVED,
            ).exists()
        )

    def test_failed_approval_rolls_back_changes_and_does_not_publish(self):
        with patch("claims.services.publish_claim_approved") as publisher:
            with self.captureOnCommitCallbacks(execute=True) as callbacks:
                with patch(
                    "claims.services.NotificationOutbox.objects.create",
                    side_effect=RuntimeError("Outbox unavailable"),
                ):
                    with self.assertRaisesMessage(RuntimeError, "Outbox unavailable"):
                        approve_claim(self.claim)

        publisher.assert_not_called()
        self.assertEqual(callbacks, [])
        self.claim.refresh_from_db()
        self.item.refresh_from_db()
        self.assertEqual(self.claim.status, Claim.Status.PENDING)
        self.assertEqual(self.item.status, Item.Status.AVAILABLE)
        self.assertFalse(HandoverTask.objects.exists())

    def test_rejected_claim_does_not_publish(self):
        reject_claim(self.claim)
        with patch("claims.services.publish_claim_approved") as publisher:
            with self.captureOnCommitCallbacks(execute=True) as callbacks:
                with self.assertRaises(ClaimTransitionError):
                    approve_claim(self.claim)

        publisher.assert_not_called()
        self.assertEqual(callbacks, [])
        self.assertFalse(HandoverTask.objects.exists())

    def test_failed_subscriber_does_not_stop_other_subscribers(self):
        event = self.make_event()
        received = []

        def failing_receiver(sender, *, event, **kwargs):
            raise RuntimeError("Consumer unavailable")

        def healthy_receiver(sender, *, event, **kwargs):
            received.append(event)

        claim_approved.connect(
            failing_receiver, dispatch_uid="test.failing_consumer", weak=False
        )
        claim_approved.connect(
            healthy_receiver, dispatch_uid="test.healthy_consumer", weak=False
        )
        try:
            with self.assertLogs("django.dispatch", level="ERROR"):
                responses = publish_claim_approved(event)
        finally:
            claim_approved.disconnect(dispatch_uid="test.failing_consumer")
            claim_approved.disconnect(dispatch_uid="test.healthy_consumer")

        self.assertEqual(received, [event])
        self.assertTrue(
            any(isinstance(response, RuntimeError) for _, response in responses)
        )
        self.assertEqual(HandoverTask.objects.count(), 1)
