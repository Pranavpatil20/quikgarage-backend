from datetime import timedelta
from decimal import Decimal

from django.db.models import Count, Sum
from django.utils import timezone
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.bookings.models import Booking, BookingStatus
from apps.invoices.models import Invoice, PaymentStatus
from apps.users.permissions import OwnerSubscriptionActive


class OwnerDashboardMetricsView(APIView):
    permission_classes = [IsAuthenticated, OwnerSubscriptionActive]

    def get(self, request):
        if not request.user.is_owner:
            return Response({'detail': 'Owner access only.'}, status=403)

        today = timezone.localdate()
        week_start = today - timedelta(days=today.weekday())

        garage_bookings = Booking.objects.filter(garage__owner=request.user)
        today_bookings = garage_bookings.filter(booking_date=today).exclude(
            status=BookingStatus.CANCELLED,
        ).count()

        pending_bookings = garage_bookings.filter(status=BookingStatus.PENDING).count()

        upcoming_bookings = garage_bookings.filter(
            booking_date__gte=today,
            status__in=[BookingStatus.PENDING, BookingStatus.CONFIRMED],
        ).count()

        customer_ids = garage_bookings.values_list('customer_id', flat=True).distinct()
        total_customers = len(set(customer_ids))

        today_revenue = Invoice.objects.filter(
            booking__garage__owner=request.user,
            booking__booking_date=today,
            payment_status=PaymentStatus.PAID,
        ).aggregate(total=Sum('total_amount'))['total'] or Decimal('0')

        weekly_revenue = Invoice.objects.filter(
            booking__garage__owner=request.user,
            booking__booking_date__gte=week_start,
            payment_status=PaymentStatus.PAID,
        ).aggregate(total=Sum('total_amount'))['total'] or Decimal('0')

        weekly_breakdown = []
        for i in range(7):
            day = week_start + timedelta(days=i)
            day_total = Invoice.objects.filter(
                booking__garage__owner=request.user,
                booking__booking_date=day,
                payment_status=PaymentStatus.PAID,
            ).aggregate(total=Sum('total_amount'))['total'] or Decimal('0')
            weekly_breakdown.append({
                'date': day.isoformat(),
                'day': day.strftime('%a'),
                'revenue': str(day_total),
            })

        recent_bookings = garage_bookings.select_related(
            'customer', 'vehicle', 'garage',
        ).order_by('-created_at')[:5]

        from apps.bookings.serializers import BookingSerializer

        return Response({
            'today_bookings': today_bookings,
            'pending_bookings': pending_bookings,
            'upcoming_bookings': upcoming_bookings,
            'total_customers': total_customers,
            'today_revenue': str(today_revenue),
            'weekly_revenue': str(weekly_revenue),
            'weekly_breakdown': weekly_breakdown,
            'recent_bookings': BookingSerializer(
                recent_bookings, many=True, context={'request': request},
            ).data,
        })
