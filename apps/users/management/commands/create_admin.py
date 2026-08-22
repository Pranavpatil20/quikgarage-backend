"""Create a Django admin superuser non-interactively."""

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = 'Create or update a superuser (phone + password).'

    def add_arguments(self, parser):
        parser.add_argument('--phone', required=True, help='Admin phone, e.g. +919876543210')
        parser.add_argument('--password', required=True, help='Admin password')
        parser.add_argument('--name', default='Admin', help='Display name')

    def handle(self, *args, **options):
        User = get_user_model()
        phone = options['phone'].strip()
        password = options['password']
        name = options['name'].strip() or 'Admin'

        if not phone:
            raise CommandError('Phone is required.')

        user, created = User.objects.get_or_create(
            phone=phone,
            defaults={'name': name, 'role': 'owner'},
        )
        user.name = name
        user.is_staff = True
        user.is_superuser = True
        user.set_password(password)
        user.save()

        verb = 'Created' if created else 'Updated'
        self.stdout.write(self.style.SUCCESS(f'{verb} superuser {phone}'))
