from django.urls import path

from .views import GarageDetailView, GarageListCreateView, MyGarageView

urlpatterns = [
    path('', GarageListCreateView.as_view(), name='garage-list'),
    path('mine/', MyGarageView.as_view(), name='garage-mine'),
    path('<int:pk>/', GarageDetailView.as_view(), name='garage-detail'),
]
