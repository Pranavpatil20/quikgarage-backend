from decimal import Decimal

from django_filters import rest_framework as filters
from rest_framework import generics

from apps.bookings.models import Booking, BookingStatus
from apps.bookings.signals import DEFAULT_SERVICE_COSTS

from .models import Invoice, PaymentStatus
from .serializers import InvoiceSerializer


class InvoiceFilter(filters.FilterSet):
    payment_status = filters.ChoiceFilter(choices=PaymentStatus.choices)

    class Meta:
        model = Invoice
        fields = ['payment_status']


class InvoiceListCreateView(generics.ListCreateAPIView):
    serializer_class = InvoiceSerializer
    filterset_class = InvoiceFilter
    search_fields = ('booking__vehicle__vehicle_number', 'booking__customer__phone')

    def get_queryset(self):
        self._ensure_invoices_for_completed(self.request.user)
        return Invoice.objects.filter(
            booking__garage__owner=self.request.user,
        ).select_related('booking__vehicle', 'booking__customer', 'booking__garage')

    def _ensure_invoices_for_completed(self, owner):
        """Backfill invoices for completed bookings that never got one."""
        completed = Booking.objects.filter(
            garage__owner=owner,
            status=BookingStatus.COMPLETED,
            invoice__isnull=True,
        )
        for booking in completed:
            service_cost = DEFAULT_SERVICE_COSTS.get(
                booking.service_type,
                Decimal('999.00'),
            )
            Invoice.objects.create(
                booking=booking,
                service_cost=service_cost,
                parts_cost=Decimal('0.00'),
                payment_status=PaymentStatus.PENDING,
            )


class InvoiceDetailView(generics.RetrieveUpdateAPIView):
    serializer_class = InvoiceSerializer

    def get_queryset(self):
        return Invoice.objects.filter(booking__garage__owner=self.request.user)
