from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from .views import (
    DevLoginView,
    FirebaseLoginView,
    PasswordLoginView,
    RefreshTokenView,
    RegisterView,
    SetupAdminView,
)

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', PasswordLoginView.as_view(), name='password-login'),
    path('dev/', DevLoginView.as_view(), name='dev-login'),
    path('firebase/', FirebaseLoginView.as_view(), name='firebase-login'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token-refresh'),
    path('refresh/', RefreshTokenView.as_view(), name='custom-refresh'),
    path('setup-admin/', SetupAdminView.as_view(), name='setup-admin'),
]
