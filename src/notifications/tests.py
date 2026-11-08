from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.test import TestCase

from items.models import Item
from claims.models import Claim
from .models import NotificationOutbox
# Create your tests here.


User = get_user_model()


class NotificationDatabaseTests(TestCase):

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
            title="Laptop",
            description="Silver laptop",
            found_location="SDU Campus"
        )

        self.claim = Claim.objects.create(
            item=self.item,
            claimant=self.claimant,
            reason="I lost my laptop"
        )

    def test_notification_created_successfully(self):
        notification = NotificationOutbox.objects.create(
            claim=self.claim,
            event_type=NotificationOutbox.EventType.CLAIM_CREATED
        )

        self.assertEqual(
            notification.status,
            NotificationOutbox.Status.PENDING
        )
        self.assertEqual(notification.claim, self.claim)
        self.assertIsNone(notification.processed_at)
        self.assertEqual(NotificationOutbox.objects.count(), 1)

    def test_duplicate_notification_is_rejected(self):
        NotificationOutbox.objects.create(
            claim=self.claim,
            event_type=NotificationOutbox.EventType.CLAIM_CREATED
        )

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                NotificationOutbox.objects.create(
                    claim=self.claim,
                    event_type=NotificationOutbox.EventType.CLAIM_CREATED
                )

        self.assertEqual(NotificationOutbox.objects.count(), 1)
