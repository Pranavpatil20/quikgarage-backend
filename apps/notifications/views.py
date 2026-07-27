from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Notification
from .serializers import NotificationSerializer


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
