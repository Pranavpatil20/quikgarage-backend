from django.urls import path

from .views import MeAPIView, SendOtpAPIView, VerifyOtpAPIView

urlpatterns = [
    path("send-otp/", SendOtpAPIView.as_view(), name="send-otp"),
    path("verify-otp/", VerifyOtpAPIView.as_view(), name="verify-otp"),
    path("me/", MeAPIView.as_view(), name="me"),
]
