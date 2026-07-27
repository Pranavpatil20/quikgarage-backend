from django.urls import path

from .views import CustomerListView, MeView, SetRoleView

urlpatterns = [
    path('me/', MeView.as_view(), name='user-me'),
    path('me/role/', SetRoleView.as_view(), name='user-set-role'),
    path('customers/', CustomerListView.as_view(), name='customer-list'),
]
