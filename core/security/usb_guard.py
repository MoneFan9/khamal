import subprocess
import logging

logger = logging.getLogger(__name__)

class USBGuardManager:
    """
    Utility class to interact with the USBGuard CLI.
    """

    @staticmethod
    def is_installed():
        """Checks if usbguard is available in the system."""
        try:
            subprocess.run(["usbguard", "--version"], capture_output=True, check=True)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False

    @staticmethod
    def generate_policy():
        """Generates a policy that allows currently connected devices."""
        try:
            result = subprocess.run(["usbguard", "generate-policy"], capture_output=True, text=True, check=True)
            return result.stdout
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to generate USBGuard policy: {e.stderr}")
            return None

    @staticmethod
    def apply_policy(policy_content):
        """Applies a given policy to /etc/usbguard/rules.conf (requires root)."""
        try:
            # We use sudo as usbguard rules usually require root privileges
            process = subprocess.Popen(["sudo", "tee", "/etc/usbguard/rules.conf"], stdin=subprocess.PIPE, text=True)
            process.communicate(input=policy_content)
            if process.returncode == 0:
                subprocess.run(["sudo", "systemctl", "restart", "usbguard"], check=True)
                return True
            return False
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to apply USBGuard policy: {e}")
            return False

    @staticmethod
    def list_devices():
        """Lists currently recognized USB devices."""
        try:
            result = subprocess.run(["usbguard", "list-devices"], capture_output=True, text=True, check=True)
            return result.stdout
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to list USB devices: {e.stderr}")
            return None

    @staticmethod
    def allow_device(device_id):
        """Allows a specific device by its ID."""
        try:
            subprocess.run(["sudo", "usbguard", "allow-device", str(device_id)], check=True)
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to allow USB device {device_id}: {e}")
            return False

    @staticmethod
    def block_device(device_id):
        """Blocks a specific device by its ID."""
        try:
            subprocess.run(["sudo", "usbguard", "block-device", str(device_id)], check=True)
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to block USB device {device_id}: {e}")
            return False
