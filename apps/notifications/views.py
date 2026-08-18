from django.conf import settings
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Notification
from .serializers import NotificationSerializer
from .tasks import send_service_due_reminders


class NotificationListView(generics.ListAPIView):
    serializer_class = NotificationSerializer

    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user)


class MarkNotificationReadView(APIView):
    def post(self, request, pk):
        try:
            notification = Notification.objects.get(pk=pk, user=request.user)
        except Notification.DoesNotExist:
            return Response({'detail': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)
        notification.read_status = True
        notification.save(update_fields=['read_status'])
        return Response(NotificationSerializer(notification).data)


class MarkAllReadView(APIView):
    def post(self, request):
        Notification.objects.filter(user=request.user, read_status=False).update(read_status=True)
        return Response({'detail': 'All notifications marked as read.'})


class ServiceReminderCronView(APIView):
    """Hit daily from Render Cron. Header: X-Cron-Secret."""

    permission_classes = [permissions.AllowAny]

    def post(self, request):
        expected = getattr(settings, 'CRON_SECRET', '') or ''
        provided = request.headers.get('X-Cron-Secret', '')
        if not expected or provided != expected:
            return Response({'detail': 'Forbidden'}, status=status.HTTP_403_FORBIDDEN)
        count = send_service_due_reminders()
        return Response({'sent': count})
