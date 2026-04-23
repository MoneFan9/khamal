from django.core.management.base import BaseCommand
from security.usb_guard import USBGuardManager

class Command(BaseCommand):
    help = "Setup USBGuard with a default policy that allows currently connected devices."

    def handle(self, *args, **options):
        if not USBGuardManager.is_installed():
            self.stderr.write(self.style.ERROR("USBGuard is not installed on this system."))
            return

        self.stdout.write("Generating initial USBGuard policy...")
        policy = USBGuardManager.generate_policy()

        if not policy:
            self.stderr.write(self.style.ERROR("Failed to generate initial policy."))
            return

        self.stdout.write("Applying initial policy...")
        if USBGuardManager.apply_policy(policy):
            self.stdout.write(self.style.SUCCESS("USBGuard setup successfully with current devices allowed."))
        else:
            self.stderr.write(self.style.ERROR("Failed to apply USBGuard policy. Ensure you have sudo privileges."))
