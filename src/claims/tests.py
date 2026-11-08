from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase

from claims.models import Claim
from claims.services import approve_claim, create_claim, reject_claim
from claims.states import ClaimTransitionError
from items.models import Item
from items.services import report_item

User = get_user_model()


class ClaimServiceTests(TestCase):

    def setUp(self):
        self.reporter = User.objects.create_user(username="reporter", password="pass")
        self.claimant = User.objects.create_user(username="claimant", password="pass")
        self.item = report_item(
            reporter=self.reporter,
            title="Phone",
            description="Black phone",
            found_location="Canteen",
        )

    def test_create_claim_is_pending(self):
        claim = create_claim(item=self.item, claimant=self.claimant, reason="Mine")
        self.assertEqual(claim.status, Claim.Status.PENDING)

    def test_reporter_cannot_claim_own_item(self):
        with self.assertRaises(ValidationError):
            create_claim(item=self.item, claimant=self.reporter, reason="Mine")

    def test_approve_marks_item_claimed(self):
        claim = create_claim(item=self.item, claimant=self.claimant, reason="Mine")
        approve_claim(claim)
        self.item.refresh_from_db()
        self.assertEqual(claim.status, Claim.Status.APPROVED)
        self.assertEqual(self.item.status, Item.Status.CLAIMED)

    def test_reject_keeps_item_available(self):
        claim = create_claim(item=self.item, claimant=self.claimant, reason="Mine")
        reject_claim(claim)
        self.item.refresh_from_db()
        self.assertEqual(claim.status, Claim.Status.REJECTED)
        self.assertEqual(self.item.status, Item.Status.AVAILABLE)

    def test_cannot_approve_rejected_claim(self):
        claim = create_claim(item=self.item, claimant=self.claimant, reason="Mine")
        reject_claim(claim)
        with self.assertRaises(ClaimTransitionError):
            approve_claim(claim)

    def test_cannot_reject_approved_claim(self):
        claim = create_claim(item=self.item, claimant=self.claimant, reason="Mine")
        approve_claim(claim)
        with self.assertRaises(ClaimTransitionError):
            reject_claim(claim)
