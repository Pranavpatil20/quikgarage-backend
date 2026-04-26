from rest_framework import generics, permissions, response

from .serializers import SendOtpSerializer, UserProfileSerializer, VerifyOtpSerializer


class SendOtpAPIView(generics.CreateAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = SendOtpSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        payload = serializer.save()
        return response.Response(
            {
                "message": "OTP sent successfully.",
                "phone_number": payload["phone_number"],
                "otp_dev_only": payload["otp"],
            }
        )


class VerifyOtpAPIView(generics.CreateAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = VerifyOtpSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return response.Response(serializer.save())


class MeAPIView(generics.RetrieveUpdateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = UserProfileSerializer

    def get_object(self):
        return self.request.user
