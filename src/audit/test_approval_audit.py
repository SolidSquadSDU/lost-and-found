from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase

from claims.events import ClaimApproved
from claims.models import Claim
from claims.publishers import publish_claim_approved
from claims.services import approve_claim, create_claim
from items.models import Item
from items.services import report_item

from .models import AuditRecord


class ApprovalAuditConsumerTests(TestCase):

    def setUp(self):
        User = get_user_model()
        self.reporter = User.objects.create_user(username="audit-reporter")
        self.claimant = User.objects.create_user(username="audit-claimant")
        self.item = report_item(
            reporter=self.reporter,
            title="Blue umbrella",
            description="Folding umbrella",
            found_location="Main hall",
        )
        self.claim = create_claim(
            item=self.item,
            claimant=self.claimant,
            reason="Name is written on the handle.",
        )

    def approve_and_capture_event(self):
        """Run a real approval; return the event that was published."""
        with patch(
            "claims.services.publish_claim_approved", wraps=publish_claim_approved
        ) as publisher:
            # TestCase wraps the test in a transaction, so run on_commit callbacks.
            with self.captureOnCommitCallbacks(execute=True):
                approve_claim(self.claim)
        publisher.assert_called_once()
        return publisher.call_args.args[0]

    def test_successful_reaction_saves_audit_record(self):
        """Approval succeeds, ClaimApproved is published, an audit record is saved."""
        event = self.approve_and_capture_event()

        # 1. main operation succeeded
        self.claim.refresh_from_db()
        self.item.refresh_from_db()
        self.assertEqual(self.claim.status, Claim.Status.APPROVED)
        self.assertEqual(self.item.status, Item.Status.CLAIMED)
        # 2. event was published
        self.assertIsInstance(event, ClaimApproved)
        # 3. consumer performed its effect
        record = AuditRecord.objects.get()
        self.assertEqual(record.event_id, event.event_id)
        self.assertEqual(record.action, AuditRecord.Action.CLAIM_APPROVED)
        self.assertEqual(record.claim_id, self.claim.pk)
        self.assertEqual(record.item_id, self.item.pk)
        self.assertEqual(record.claimant_id, self.claimant.pk)
        self.assertEqual(record.reporter_id, self.reporter.pk)
        self.assertEqual(record.occurred_at, event.occurred_at)

    def test_duplicate_delivery_saves_only_one_audit_record(self):
        """Delivering the same event twice must not write a second record."""
        event = self.approve_and_capture_event()
        first = AuditRecord.objects.get()

        # Redeliver the exact same event. send_robust() hides receiver errors,
        # so also check that no receiver failed instead of handling it quietly.
        responses = publish_claim_approved(event)

        self.assertFalse(
            any(isinstance(response, Exception) for _, response in responses)
        )
        self.assertEqual(AuditRecord.objects.count(), 1)
        same = AuditRecord.objects.get()
        self.assertEqual(same.pk, first.pk)
        self.assertEqual(same.recorded_at, first.recorded_at)
