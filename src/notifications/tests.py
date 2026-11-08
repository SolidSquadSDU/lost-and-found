from django.contrib.auth import get_user_model
from django.test import TestCase

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
        approve_claim(self.claim)
        self.assertTrue(self.has_event(NotificationOutbox.EventType.CLAIM_APPROVED))

    def test_reject_claim_writes_claim_rejected(self):
        reject_claim(self.claim)
        self.assertTrue(self.has_event(NotificationOutbox.EventType.CLAIM_REJECTED))
