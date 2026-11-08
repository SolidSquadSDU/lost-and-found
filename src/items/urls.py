from django.urls import path

from . import views

urlpatterns = [
    path("", views.item_list, name="item_list"),
    path("report/", views.report_item_view, name="report_item"),
    path("<int:item_id>/", views.item_detail, name="item_detail"),
    # TODO: add JSON API routes for mobile clients
]
