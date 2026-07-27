from django.urls import path

from .views import (
    AvailableSlotsView,
    CustomerBookingDetailView,
    CustomerBookingListCreateView,
    OwnerBookingCreateView,
    OwnerBookingListView,
    OwnerBookingStatusView,
    TodayBookingsView,
)

urlpatterns = [
    path('', CustomerBookingListCreateView.as_view(), name='booking-list'),
    path('today/', TodayBookingsView.as_view(), name='booking-today'),
    path('<int:pk>/', CustomerBookingDetailView.as_view(), name='booking-detail'),
    path('owner/', OwnerBookingListView.as_view(), name='owner-booking-list'),
    path('owner/create/', OwnerBookingCreateView.as_view(), name='owner-booking-create'),
    path('owner/<int:pk>/status/', OwnerBookingStatusView.as_view(), name='owner-booking-status'),
    path('slots/<int:garage_id>/', AvailableSlotsView.as_view(), name='available-slots'),
]
