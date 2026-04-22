from django.core.management.base import BaseCommand
from projects.services import ensure_global_proxy

class Command(BaseCommand):
    help = 'Sets up the global Traefik proxy and its network.'

    def handle(self, *args, **options):
        self.stdout.write("Setting up global Traefik proxy...")
        try:
            ensure_global_proxy()
            self.stdout.write(self.style.SUCCESS("Global Traefik proxy is set up and running."))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Failed to set up Traefik proxy: {e}"))
