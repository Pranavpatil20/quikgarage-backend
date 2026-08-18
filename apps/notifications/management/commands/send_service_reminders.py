from django.core.management.base import BaseCommand

from apps.notifications.tasks import send_service_due_reminders


class Command(BaseCommand):
    help = 'Send outside-app reminders for services completed ~3 months ago.'

    def handle(self, *args, **options):
        count = send_service_due_reminders()
        self.stdout.write(self.style.SUCCESS(f'Sent {count} service-due reminders.'))
