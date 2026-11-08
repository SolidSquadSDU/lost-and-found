#Don't touch its for database testing
from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.db.models.deletion import ProtectedError
from django.test import TestCase

from items.models import Item
from .models import Claim

# Create your tests here.

User = get_user_model()


class ClaimDatabaseTests(TestCase):

    def setUp(self):
        self.reporter = User.objects.create_user(
            username="reporter",
            password="testpass123"
        )

        self.claimant = User.objects.create_user(
            username="claimant",
            password="testpass123"
        )

        self.item = Item.objects.create(
            reporter=self.reporter,
            title="iPhone 17",
            description="Black smartphone",
            found_location="SDU Library"
        )

    def test_create_claim_successfully(self):
        claim = Claim.objects.create(
            item=self.item,
            claimant=self.claimant,
            reason="This is my phone"
        )

        self.assertEqual(claim.status, Claim.Status.PENDING)
        self.assertEqual(claim.item, self.item)
        self.assertEqual(claim.claimant, self.claimant)
        self.assertEqual(self.item.claims.count(), 1)

    def test_duplicate_claim_is_rejected(self):
        Claim.objects.create(
            item=self.item,
            claimant=self.claimant,
            reason="First claim"
        )

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Claim.objects.create(
                    item=self.item,
                    claimant=self.claimant,
                    reason="Duplicate claim"
                )

        self.assertEqual(Claim.objects.count(), 1)

    def test_item_with_claim_cannot_be_deleted(self):
        Claim.objects.create(
            item=self.item,
            claimant=self.claimant,
            reason="My phone"
        )

        with self.assertRaises(ProtectedError):
            self.item.delete()

        self.assertTrue(
            Item.objects.filter(pk=self.item.pk).exists()
        )
