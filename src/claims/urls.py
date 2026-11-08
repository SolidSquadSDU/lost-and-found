from django.urls import path

from . import views

urlpatterns = [
    path("pending/", views.pending_claims_view, name="pending_claims"),
    path("item/<int:item_id>/create/", views.create_claim_view, name="create_claim"),
    path("<int:claim_id>/approve/", views.approve_claim_view, name="approve_claim"),
    path("<int:claim_id>/reject/", views.reject_claim_view, name="reject_claim"),
    # TODO: add claim detail page with notification history
]
