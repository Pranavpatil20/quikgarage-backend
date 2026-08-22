from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import User
from .permissions import OwnerSubscriptionActive
from .serializers import RoleSelectionSerializer, UserProfileUpdateSerializer, UserSerializer


class MeView(generics.RetrieveUpdateAPIView):
    serializer_class = UserSerializer

    def get_object(self):
        return self.request.user

    def get_serializer_class(self):
        if self.request.method in ('PUT', 'PATCH'):
            return UserProfileUpdateSerializer
        return UserSerializer

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        serializer = UserProfileUpdateSerializer(
            request.user, data=request.data, partial=partial,
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(UserSerializer(request.user).data)


class SetRoleView(APIView):
    def post(self, request):
        serializer = RoleSelectionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = request.user
        if user.role and user.garages.exists() if hasattr(user, 'garages') else False:
            pass
        user.role = serializer.validated_data['role']
        user.save(update_fields=['role', 'updated_at'])
        return Response(UserSerializer(user).data)


class CustomerListView(generics.ListAPIView):
    """Owner: list customers who booked at owner's garage."""
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated, OwnerSubscriptionActive]
    search_fields = ('name', 'phone')

    def get_queryset(self):
        user = self.request.user
        if not user.is_owner:
            return User.objects.none()
        from apps.bookings.models import Booking
        customer_ids = Booking.objects.filter(
            garage__owner=user,
        ).values_list('customer_id', flat=True).distinct()
        return User.objects.filter(id__in=customer_ids).exclude(role='owner')
