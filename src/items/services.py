from .models import Item


def report_item(*, reporter, title, description, found_location):
    """Store a newly reported found item as AVAILABLE."""
    return Item.objects.create(
        reporter=reporter,
        title=title,
        description=description,
        found_location=found_location,
        status=Item.Status.AVAILABLE,
    )
