import os
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

User = get_user_model()

class Command(BaseCommand):
    help = 'Creates a system administrator based on environment variables'

    def handle(self, *args, **options):
        username = os.environ.get('SYSTEM_ADMIN_USERNAME')
        password = os.environ.get('SYSTEM_ADMIN_PASSWORD')
        email = os.environ.get('SYSTEM_ADMIN_EMAIL', 'admin@khamal.internal')

        if not username or not password:
            self.stdout.write(self.style.WARNING(
                "SYSTEM_ADMIN_USERNAME or SYSTEM_ADMIN_PASSWORD not set. Skipping system admin creation."
            ))
            return

        if User.objects.filter(username=username).exists():
            user = User.objects.get(username=username)
            user.email = email
            user.set_password(password)
            user.is_superuser = True
            user.is_staff = True
            user.save()
            self.stdout.write(self.style.SUCCESS(f"System admin '{username}' updated successfully."))
        else:
            User.objects.create_superuser(
                username=username,
                email=email,
                password=password
            )
            self.stdout.write(self.style.SUCCESS(f"System admin '{username}' created successfully."))
