from datetime import timedelta

from django.utils import timezone
from rest_framework import decorators, permissions, response, status, viewsets

from apps.common.services import send_whatsapp_message
from .models import Booking, Invoice
from .serializers import (
    BookingSerializer,
    BookingStatusSerializer,
    DashboardSerializer,
    InvoiceSerializer,
    SlotAvailabilitySerializer,
)


class BookingViewSet(viewsets.ModelViewSet):
    serializer_class = BookingSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ["status", "booking_date"]

    def get_queryset(self):
        user = self.request.user
        if user.role == "owner":
            return Booking.objects.filter(owner=user).select_related("customer", "vehicle")
        return Booking.objects.filter(customer__user=user).select_related("owner", "vehicle")

    def update(self, request, *args, **kwargs):
        return response.Response({"detail": "Direct update is not allowed."}, status=status.HTTP_405_METHOD_NOT_ALLOWED)

    def partial_update(self, request, *args, **kwargs):
        return response.Response({"detail": "Direct update is not allowed."}, status=status.HTTP_405_METHOD_NOT_ALLOWED)

    def destroy(self, request, *args, **kwargs):
        return response.Response({"detail": "Delete is not allowed."}, status=status.HTTP_405_METHOD_NOT_ALLOWED)

    def perform_create(self, serializer):
        booking = serializer.save()
        send_whatsapp_message(
            booking.customer.user.phone_number,
            f"Your servicing booking is confirmed on {booking.booking_date} at {booking.time_slot}.",
        )

    @decorators.action(detail=True, methods=["post"])
    def start_service(self, request, pk=None):
        if request.user.role != "owner":
            return response.Response({"detail": "Only owner can start service."}, status=status.HTTP_403_FORBIDDEN)
        booking = self.get_object()
        serializer = BookingStatusSerializer(booking, data={"status": "in_progress"}, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        send_whatsapp_message(booking.customer.user.phone_number, "Your vehicle service has started.")
        return response.Response({"message": "Service started."})

    @decorators.action(detail=True, methods=["post"])
    def complete(self, request, pk=None):
        if request.user.role != "owner":
            return response.Response({"detail": "Only owner can complete booking."}, status=status.HTTP_403_FORBIDDEN)
        booking = self.get_object()
        serializer = BookingStatusSerializer(booking, data={"status": "completed"}, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        send_whatsapp_message(booking.customer.user.phone_number, "Your service is completed. Thank you.")
        return response.Response({"message": "Booking marked completed. Proceed to billing."})

    @decorators.action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        if request.user.role == "customer" and self.get_object().status == "in_progress":
            return response.Response(
                {"detail": "Cannot cancel booking after service starts."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        booking = self.get_object()
        serializer = BookingStatusSerializer(booking, data={"status": "cancelled"}, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        send_whatsapp_message(booking.customer.user.phone_number, "Your booking has been cancelled.")
        return response.Response({"message": "Booking cancelled."})

    @decorators.action(detail=False, methods=["get"])
    def dashboard(self, request):
        if request.user.role != "owner":
            return response.Response({"detail": "Owner access only."}, status=status.HTTP_403_FORBIDDEN)
        today = timezone.localdate()
        week_start = today - timedelta(days=today.weekday())
        data = DashboardSerializer.build(request.user, today, week_start)
        return response.Response(data)

    @decorators.action(detail=False, methods=["get"], url_path="slots")
    def slots(self, request):
        if request.user.role != "owner":
            return response.Response({"detail": "Owner access only."}, status=status.HTTP_403_FORBIDDEN)
        date_str = request.query_params.get("date")
        if not date_str:
            return response.Response({"detail": "date query param is required (YYYY-MM-DD)."}, status=400)
        try:
            booking_date = timezone.datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            return response.Response({"detail": "Invalid date format. Use YYYY-MM-DD."}, status=400)
        return response.Response(SlotAvailabilitySerializer.build(request.user, booking_date))


class InvoiceViewSet(viewsets.ModelViewSet):
    serializer_class = InvoiceSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.role == "owner":
            return Invoice.objects.filter(booking__owner=user).select_related("booking")
        return Invoice.objects.filter(booking__customer__user=user).select_related("booking")

    def create(self, request, *args, **kwargs):
        if request.user.role != "owner":
            return response.Response({"detail": "Only owner can create invoice."}, status=status.HTTP_403_FORBIDDEN)
        booking_id = request.data.get("booking")
        booking = Booking.objects.filter(id=booking_id, owner=request.user).first()
        if not booking:
            return response.Response({"detail": "Booking not found."}, status=status.HTTP_404_NOT_FOUND)
        result = super().create(request, *args, **kwargs)
        send_whatsapp_message(
            booking.customer.user.phone_number,
            "Your service is completed. Please check your bill details in app.",
        )
        return result
