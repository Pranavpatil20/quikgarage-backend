from django_filters import rest_framework as filters
from rest_framework import generics

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
        return Invoice.objects.filter(
            booking__garage__owner=self.request.user,
        ).select_related('booking__vehicle', 'booking__customer', 'booking__garage')


class InvoiceDetailView(generics.RetrieveUpdateAPIView):
    serializer_class = InvoiceSerializer

    def get_queryset(self):
        return Invoice.objects.filter(booking__garage__owner=self.request.user)
