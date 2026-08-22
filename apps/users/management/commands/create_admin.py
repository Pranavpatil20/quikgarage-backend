"""Create a Django admin superuser non-interactively."""

from django.core.management.base import BaseCommand, CommandError

from apps.users.admin_setup import create_or_update_superuser


class Command(BaseCommand):
    help = 'Create or update a superuser (phone + password).'

    def add_arguments(self, parser):
        parser.add_argument('--phone', required=True, help='Admin phone, e.g. +919876543210')
        parser.add_argument('--password', required=True, help='Admin password')
        parser.add_argument('--name', default='Admin', help='Display name')

    def handle(self, *args, **options):
        try:
            user, created = create_or_update_superuser(
                phone=options['phone'],
                password=options['password'],
                name=options['name'],
            )
        except ValueError as exc:
            raise CommandError(str(exc)) from exc

        verb = 'Created' if created else 'Updated'
        self.stdout.write(self.style.SUCCESS(f'{verb} superuser {user.phone}'))
