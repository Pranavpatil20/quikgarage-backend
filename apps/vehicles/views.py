from rest_framework import generics

from .models import Vehicle
from .serializers import VehicleSerializer


class VehicleListCreateView(generics.ListCreateAPIView):
    serializer_class = VehicleSerializer

    def get_queryset(self):
        return Vehicle.objects.filter(customer=self.request.user)


class VehicleDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = VehicleSerializer

    def get_queryset(self):
        return Vehicle.objects.filter(customer=self.request.user)
