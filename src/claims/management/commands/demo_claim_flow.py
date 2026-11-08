from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from claims.services import approve_claim, create_claim
from items.services import report_item
from notifications.models import NotificationOutbox


class Command(BaseCommand):
    help = "Run the report → claim → approve prototype flow and print the result."

    def handle(self, *args, **options):
        User = get_user_model()
        reporter, _ = User.objects.get_or_create(
            username="reporter",
            defaults={"email": "reporter@campus.local"},
        )
        claimant, _ = User.objects.get_or_create(
            username="claimant",
            defaults={"email": "claimant@campus.local"},
        )

        item = report_item(
            reporter=reporter,
            title="Black backpack",
            description="Nike backpack with a blue keychain",
            found_location="Library 2nd floor",
        )
        claim = create_claim(
            item=item,
            claimant=claimant,
            reason="My student ID and laptop stickers are inside.",
        )
        claim = approve_claim(claim)
        item.refresh_from_db()

        notifications = NotificationOutbox.objects.filter(claim=claim).order_by("id")

        self.stdout.write(self.style.SUCCESS("Demo claim flow completed"))
        self.stdout.write(f"Item #{item.id}: {item.title} [{item.status}]")
        self.stdout.write(f"Claim #{claim.id}: {claim.status} by {claimant.username}")
        for note in notifications:
            self.stdout.write(f"Notification: {note.event_type} [{note.status}]")
