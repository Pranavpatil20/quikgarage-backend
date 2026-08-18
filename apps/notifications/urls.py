from django.urls import path

from .views import (
    MarkAllReadView,
    MarkNotificationReadView,
    NotificationListView,
    ServiceReminderCronView,
)

urlpatterns = [
    path('', NotificationListView.as_view(), name='notification-list'),
    path('read-all/', MarkAllReadView.as_view(), name='notification-read-all'),
    path('cron/service-reminders/', ServiceReminderCronView.as_view(), name='service-reminder-cron'),
    path('<int:pk>/read/', MarkNotificationReadView.as_view(), name='notification-read'),
]
