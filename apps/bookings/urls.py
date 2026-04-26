from rest_framework.routers import DefaultRouter

from .views import BookingViewSet, InvoiceViewSet

router = DefaultRouter()
router.register("invoices", InvoiceViewSet, basename="invoices")
router.register("", BookingViewSet, basename="bookings")

urlpatterns = router.urls
