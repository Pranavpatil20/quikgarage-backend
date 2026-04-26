from rest_framework import generics, permissions, viewsets

from apps.common.permissions import IsCustomer
from apps.common.permissions import IsOwner
from .models import CustomerProfile, Vehicle
from .serializers import CustomerSelfProfileSerializer, CustomerSerializer, VehicleSerializer


class CustomerViewSet(viewsets.ModelViewSet):
    serializer_class = CustomerSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwner]

    def get_queryset(self):
        return CustomerProfile.objects.filter(owner=self.request.user).select_related("user").prefetch_related("vehicles")


class CustomerSelfProfileAPIView(generics.RetrieveUpdateAPIView):
    serializer_class = CustomerSelfProfileSerializer
    permission_classes = [permissions.IsAuthenticated, IsCustomer]

    def get_object(self):
        return CustomerProfile.objects.select_related("user").get(user=self.request.user)


class VehicleViewSet(viewsets.ModelViewSet):
    serializer_class = VehicleSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if self.request.user.role == "customer":
            customer = CustomerProfile.objects.filter(user=self.request.user).first()
            if not customer:
                return Vehicle.objects.none()
            return Vehicle.objects.filter(customer=customer)
        return Vehicle.objects.filter(customer__owner=self.request.user)

    def perform_create(self, serializer):
        if self.request.user.role == "customer":
            customer = CustomerProfile.objects.filter(user=self.request.user).first()
            serializer.save(customer=customer)
        else:
            serializer.save()
