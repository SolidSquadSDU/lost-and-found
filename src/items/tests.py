from django.contrib.auth import get_user_model
from django.test import TestCase

from items.models import Item
from items.services import report_item

User = get_user_model()


class ReportItemTests(TestCase):

    def setUp(self):
        self.reporter = User.objects.create_user(username="reporter", password="pass")

    def test_report_item_saves_item(self):
        item = report_item(
            reporter=self.reporter,
            title="Black backpack",
            description="Has a laptop inside",
            found_location="Library",
        )
        self.assertEqual(Item.objects.count(), 1)
        self.assertEqual(item.title, "Black backpack")
        self.assertEqual(item.reporter, self.reporter)

    def test_reported_item_starts_as_available(self):
        item = report_item(
            reporter=self.reporter,
            title="Keys",
            description="Two keys",
            found_location="Gym",
        )
        self.assertEqual(item.status, Item.Status.AVAILABLE)
