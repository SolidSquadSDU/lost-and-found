from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from .models import Item
from .services import report_item


def item_list(request):
    # TODO: paginate and filter by status/location
    items = Item.objects.select_related("reporter").order_by("-created_at")
    return render(request, "items/list.html", {"items": items})


def item_detail(request, item_id):
    item = get_object_or_404(Item.objects.select_related("reporter"), pk=item_id)
    claims = item.claims.select_related("claimant").order_by("-created_at")
    return render(
        request,
        "items/detail.html",
        {"item": item, "claims": claims},
    )


@login_required
def report_item_view(request):
    if request.method == "POST":
        # TODO: validate with a Django Form class
        item = report_item(
            reporter=request.user,
            title=request.POST.get("title", "").strip(),
            description=request.POST.get("description", "").strip(),
            found_location=request.POST.get("found_location", "").strip(),
        )
        messages.success(request, f"Reported item #{item.id}.")
        return redirect("item_detail", item_id=item.id)
    return render(request, "items/report.html")
