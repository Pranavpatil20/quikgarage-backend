from django.urls import path

from .views import InvoiceDetailView, InvoiceListCreateView

urlpatterns = [
    path('', InvoiceListCreateView.as_view(), name='invoice-list'),
    path('<int:pk>/', InvoiceDetailView.as_view(), name='invoice-detail'),
]
