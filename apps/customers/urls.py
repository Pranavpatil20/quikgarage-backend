from rest_framework.routers import DefaultRouter

from .views import CustomerSelfProfileAPIView, CustomerViewSet, VehicleViewSet
from django.urls import path

router = DefaultRouter()
router.register("", CustomerViewSet, basename="customers")

urlpatterns = [
    path("me/", CustomerSelfProfileAPIView.as_view(), name="customer-self-profile"),
    path(
        "vehicles/",
        VehicleViewSet.as_view({"get": "list", "post": "create"}),
        name="vehicles-list-create",
    ),
    path(
        "vehicles/<int:pk>/",
        VehicleViewSet.as_view({"patch": "partial_update", "delete": "destroy"}),
        name="vehicles-update-delete",
    ),
]
urlpatterns += router.urls
