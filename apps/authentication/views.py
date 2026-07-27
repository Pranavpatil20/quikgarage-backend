from django.conf import settings
from django.contrib.auth import get_user_model
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from apps.users.serializers import UserSerializer

from .serializers import FirebaseAuthSerializer, PhoneAuthSerializer

User = get_user_model()


def _issue_tokens(user):
    refresh = RefreshToken.for_user(user)
    return {
        'access': str(refresh.access_token),
        'refresh': str(refresh),
        'user': UserSerializer(user).data,
    }


class FirebaseLoginView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = FirebaseAuthSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        user, created = User.objects.get_or_create(
            phone=data['phone'],
            defaults={
                'name': data.get('name', ''),
                'role': data.get('role', 'customer'),
                'firebase_uid': data['firebase_uid'],
            },
        )
        if not created:
            update_fields = []
            if data.get('firebase_uid') and user.firebase_uid != data['firebase_uid']:
                user.firebase_uid = data['firebase_uid']
                update_fields.append('firebase_uid')
            if data.get('name') and not user.name:
                user.name = data['name']
                update_fields.append('name')
            if data.get('role'):
                user.role = data['role']
                update_fields.append('role')
            if data.get('fcm_token'):
                user.fcm_token = data['fcm_token']
                update_fields.append('fcm_token')
            if update_fields:
                user.save(update_fields=update_fields + ['updated_at'])

        return Response({
            **_issue_tokens(user),
            'is_new_user': created,
        })


class DevLoginView(APIView):
    """DEBUG-only: sign in with phone number without Firebase (local development)."""

    permission_classes = [permissions.AllowAny]

    def post(self, request):
        if not settings.DEBUG:
            return Response(
                {'detail': 'Dev login is disabled in production.'},
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = PhoneAuthSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        phone = data['phone'].strip().replace(' ', '')
        if not phone.startswith('+'):
            phone = f'+91{phone.lstrip("0")}'

        user, created = User.objects.get_or_create(
            phone=phone,
            defaults={
                'name': data.get('name', ''),
                'role': data.get('role', 'customer'),
                'firebase_uid': f'dev_{phone}',
            },
        )
        if not created:
            update_fields = []
            if data.get('name') and not user.name:
                user.name = data['name']
                update_fields.append('name')
            if data.get('role'):
                user.role = data['role']
                update_fields.append('role')
            if update_fields:
                user.save(update_fields=update_fields + ['updated_at'])

        return Response({
            **_issue_tokens(user),
            'is_new_user': created,
        })


class RefreshTokenView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        refresh_token = request.data.get('refresh')
        if not refresh_token:
            return Response({'detail': 'refresh token required'}, status=400)
        try:
            refresh = RefreshToken(refresh_token)
            return Response({'access': str(refresh.access_token)})
        except Exception:
            return Response({'detail': 'Invalid refresh token'}, status=401)
