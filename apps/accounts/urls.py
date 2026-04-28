from django.urls import path

from .views import MeAPIView, SendOtpAPIView, VerifyFirebaseOtpAPIView, VerifyOtpAPIView

urlpatterns = [
    path("send-otp/", SendOtpAPIView.as_view(), name="send-otp"),
    path("verify-otp/", VerifyOtpAPIView.as_view(), name="verify-otp"),
    path("verify-firebase-otp/", VerifyFirebaseOtpAPIView.as_view(), name="verify-firebase-otp"),
    path("me/", MeAPIView.as_view(), name="me"),
]
