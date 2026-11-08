from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404, redirect, render

from items.models import Item

from .models import Claim
from .services import approve_claim, create_claim, reject_claim
from .states import ClaimTransitionError


@login_required
def create_claim_view(request, item_id):
    item = get_object_or_404(Item, pk=item_id)
    if request.method != "POST":
        return redirect("item_detail", item_id=item.id)

    try:
        # TODO: validate reason length / required proof fields
        claim = create_claim(
            item=item,
            claimant=request.user,
            reason=request.POST.get("reason", "").strip(),
        )
        messages.success(request, f"Claim #{claim.id} submitted.")
    except ValidationError as exc:
        messages.error(request, "; ".join(exc.messages))
    return redirect("item_detail", item_id=item.id)


@login_required
def approve_claim_view(request, claim_id):
    claim = get_object_or_404(Claim.objects.select_related("item"), pk=claim_id)
    # TODO: restrict approve/reject to staff or the item reporter only in a permission layer
    if request.method == "POST":
        try:
            approve_claim(claim)
            messages.success(request, f"Claim #{claim.id} approved.")
        except ClaimTransitionError as exc:
            messages.error(request, str(exc))
    return redirect("item_detail", item_id=claim.item_id)


@login_required
def reject_claim_view(request, claim_id):
    claim = get_object_or_404(Claim.objects.select_related("item"), pk=claim_id)
    if request.method == "POST":
        try:
            reject_claim(claim)
            messages.success(request, f"Claim #{claim.id} rejected.")
        except ClaimTransitionError as exc:
            messages.error(request, str(exc))
    return redirect("item_detail", item_id=claim.item_id)


@login_required
def pending_claims_view(request):
    # TODO: filter to claims on items owned by request.user
    claims = (
        Claim.objects.filter(status=Claim.Status.PENDING)
        .select_related("item", "claimant", "item__reporter")
        .order_by("-created_at")
    )
    return render(request, "claims/pending.html", {"claims": claims})
