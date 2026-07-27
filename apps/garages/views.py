from rest_framework import generics, permissions

from .models import Garage
from .serializers import GarageSerializer


class GarageListCreateView(generics.ListCreateAPIView):
    serializer_class = GarageSerializer

    def get_queryset(self):
        user = self.request.user
        if user.is_owner:
            return Garage.objects.filter(owner=user)
        return Garage.objects.all()


class GarageDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = GarageSerializer

    def get_queryset(self):
        user = self.request.user
        if user.is_owner:
            return Garage.objects.filter(owner=user)
        return Garage.objects.all()


class MyGarageView(generics.RetrieveAPIView):
    """Owner's primary garage."""
    serializer_class = GarageSerializer

    def get_object(self):
        garage = Garage.objects.filter(owner=self.request.user).first()
        if not garage:
            from rest_framework.exceptions import NotFound
            raise NotFound('No garage configured. Create one first.')
        return garage
