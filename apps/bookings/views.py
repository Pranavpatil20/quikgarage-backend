from django.utils import timezone
from django_filters import rest_framework as filters
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.users.permissions import OwnerSubscriptionActive
from apps.users.subscription import owner_has_active_subscription

from .models import Booking, BookingStatus
from .serializers import (
    BookingSerializer,
    BookingStatusUpdateSerializer,
    OwnerBookingCreateSerializer,
)
from .services import get_available_slots


class BookingFilter(filters.FilterSet):
    status = filters.ChoiceFilter(choices=BookingStatus.choices)
    booking_date = filters.DateFilter()
    booking_date_gte = filters.DateFilter(field_name='booking_date', lookup_expr='gte')
    booking_date_lte = filters.DateFilter(field_name='booking_date', lookup_expr='lte')
    customer = filters.NumberFilter(field_name='customer_id')

    class Meta:
        model = Booking
        fields = ['status', 'booking_date', 'garage', 'customer']


class CustomerBookingListCreateView(generics.ListCreateAPIView):
    serializer_class = BookingSerializer
    filterset_class = BookingFilter
    search_fields = ('vehicle__vehicle_number', 'service_type')

    def get_queryset(self):
        return Booking.objects.filter(
            customer=self.request.user,
        ).select_related('garage', 'vehicle', 'customer')


class CustomerBookingDetailView(generics.RetrieveDestroyAPIView):
    serializer_class = BookingSerializer

    def get_queryset(self):
        return Booking.objects.filter(customer=self.request.user)

    def perform_destroy(self, instance):
        if not instance.can_customer_cancel:
            from rest_framework.exceptions import ValidationError
            raise ValidationError('Cannot cancel after service has started.')
        instance.status = BookingStatus.CANCELLED
        instance.save(update_fields=['status', 'updated_at'])


class OwnerBookingListView(generics.ListAPIView):
    serializer_class = BookingSerializer
    filterset_class = BookingFilter
    search_fields = ('customer__name', 'customer__phone', 'vehicle__vehicle_number')
    permission_classes = [permissions.IsAuthenticated, OwnerSubscriptionActive]

    def get_queryset(self):
        return Booking.objects.filter(
            garage__owner=self.request.user,
        ).select_related('garage', 'vehicle', 'customer')


class OwnerBookingCreateView(generics.CreateAPIView):
    serializer_class = OwnerBookingCreateSerializer
    permission_classes = [permissions.IsAuthenticated, OwnerSubscriptionActive]

    def get_queryset(self):
        return Booking.objects.filter(garage__owner=self.request.user)


class OwnerBookingStatusView(generics.UpdateAPIView):
    serializer_class = BookingStatusUpdateSerializer
    http_method_names = ['patch', 'put']
    permission_classes = [permissions.IsAuthenticated, OwnerSubscriptionActive]

    def get_queryset(self):
        return Booking.objects.filter(garage__owner=self.request.user)


class AvailableSlotsView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, garage_id):
        from apps.garages.models import Garage

        try:
            garage = Garage.objects.select_related('owner').get(pk=garage_id)
        except Garage.DoesNotExist:
            return Response({'detail': 'Garage not found.'}, status=status.HTTP_404_NOT_FOUND)

        if not owner_has_active_subscription(garage.owner):
            return Response(
                {'detail': 'Garage is not available for booking.', 'code': 'subscription_required'},
                status=status.HTTP_403_FORBIDDEN,
            )

        date_str = request.query_params.get('date')
        if not date_str:
            return Response({'detail': 'date query param required (YYYY-MM-DD).'}, status=400)
        from datetime import datetime
        booking_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        slots = get_available_slots(garage, booking_date)
        return Response({'garage_id': garage_id, 'date': date_str, 'slots': slots})


class TodayBookingsView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        today = timezone.localdate()
        if request.user.is_owner:
            if not owner_has_active_subscription(request.user):
                return Response(
                    {'detail': 'Subscription payment required.', 'code': 'subscription_required'},
                    status=status.HTTP_403_FORBIDDEN,
                )
            qs = Booking.objects.filter(
                garage__owner=request.user,
                booking_date=today,
            ).exclude(status=BookingStatus.CANCELLED)
        else:
            qs = Booking.objects.filter(customer=request.user, booking_date=today)
        serializer = BookingSerializer(qs.select_related('garage', 'vehicle', 'customer'), many=True)
        return Response(serializer.data)
