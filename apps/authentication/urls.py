from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from .views import DevLoginView, FirebaseLoginView, RefreshTokenView

urlpatterns = [
    path('dev/', DevLoginView.as_view(), name='dev-login'),
    path('firebase/', FirebaseLoginView.as_view(), name='firebase-login'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token-refresh'),
    path('refresh/', RefreshTokenView.as_view(), name='custom-refresh'),
]
