from rest_framework import generics, permissions

from apps.users.permissions import OwnerSubscriptionActive
from apps.users.subscription import filter_garages_for_customers

from .models import Garage
from .serializers import GarageSerializer


class GarageListCreateView(generics.ListCreateAPIView):
    serializer_class = GarageSerializer

    def get_permissions(self):
        user = self.request.user
        if self.request.method == 'POST' or getattr(user, 'is_owner', False):
            return [permissions.IsAuthenticated(), OwnerSubscriptionActive()]
        return [permissions.IsAuthenticated()]

    def get_queryset(self):
        user = self.request.user
        if user.is_owner:
            return Garage.objects.filter(owner=user)
        return filter_garages_for_customers(Garage.objects.all())


class GarageDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = GarageSerializer
    permission_classes = [permissions.IsAuthenticated, OwnerSubscriptionActive]

    def get_queryset(self):
        user = self.request.user
        if user.is_owner:
            return Garage.objects.filter(owner=user)
        return filter_garages_for_customers(Garage.objects.all())


class MyGarageView(generics.RetrieveAPIView):
    """Owner's primary garage."""
    serializer_class = GarageSerializer
    permission_classes = [permissions.IsAuthenticated, OwnerSubscriptionActive]

    def get_object(self):
        garage = Garage.objects.filter(owner=self.request.user).first()
        if not garage:
            from rest_framework.exceptions import NotFound
            raise NotFound('No garage configured. Create one first.')
        return garage
