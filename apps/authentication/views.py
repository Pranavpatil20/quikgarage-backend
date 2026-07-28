import os
from datetime import time

from django.conf import settings
from django.contrib.auth import get_user_model
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from apps.garages.models import Garage
from apps.users.models import UserRole
from apps.users.serializers import UserSerializer

from .serializers import (
    FirebaseAuthSerializer,
    PasswordLoginSerializer,
    PhoneAuthSerializer,
    RegisterSerializer,
    normalize_phone,
)

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
            phone=normalize_phone(data['phone']),
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
    """Phone login without Firebase (local / staging when ENABLE_DEV_AUTH=true)."""

    permission_classes = [permissions.AllowAny]

    def post(self, request):
        allow_dev = settings.DEBUG or os.getenv('ENABLE_DEV_AUTH', 'false').lower() == 'true'
        if not allow_dev:
            return Response(
                {'detail': 'Dev login is disabled. Set ENABLE_DEV_AUTH=true or use Firebase OTP.'},
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = PhoneAuthSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        phone = normalize_phone(data['phone'])

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


class RegisterView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        phone = normalize_phone(data['phone'])

        if User.objects.filter(phone=phone).exists():
            return Response(
                {'detail': 'An account with this phone number already exists. Please sign in.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = User.objects.create_user(
            phone=phone,
            name=data['name'].strip(),
            role=data['role'],
            password=data['password'],
            firebase_uid=f'pwd_{phone}',
        )

        if data['role'] == UserRole.OWNER:
            Garage.objects.create(
                owner=user,
                garage_name=data['garage_name'].strip(),
                address='Address not set yet',
                opening_time=time(9, 0),
                closing_time=time(18, 0),
            )

        return Response({
            **_issue_tokens(user),
            'is_new_user': True,
        }, status=status.HTTP_201_CREATED)


class PasswordLoginView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = PasswordLoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        phone = normalize_phone(data['phone'])
        role = data['role']

        try:
            user = User.objects.get(phone=phone)
        except User.DoesNotExist:
            return Response(
                {'detail': 'No account found with this phone number. Please sign up first.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        if not user.has_usable_password() or not user.check_password(data['password']):
            return Response(
                {'detail': 'Incorrect phone number or password.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if user.role != role:
            if user.role == UserRole.OWNER:
                message = 'You are not a customer. Please sign in as Owner.'
            else:
                message = 'You are not an owner. Please sign in as Customer.'
            return Response({'detail': message}, status=status.HTTP_403_FORBIDDEN)

        return Response({
            **_issue_tokens(user),
            'is_new_user': False,
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
