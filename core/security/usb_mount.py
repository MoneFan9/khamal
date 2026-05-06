import subprocess
import logging
import os
from .usb_guard import USBGuardManager

logger = logging.getLogger(__name__)

class USBMountManager:
    """
    Utility class to securely mount USB volumes.
    Forces noexec, nosuid, and nodev options to prevent malware execution.
    """

    @staticmethod
    def _validate_paths(device_path, mount_point):
        """
        Validates device and mount paths for security.
        """
        try:
            device_path = os.path.normpath(device_path)
            if not os.path.isabs(mount_point):
                logger.error(f"Mount point must be absolute: {mount_point}")
                return None, None

            normalized_mount = os.path.normpath(mount_point)
        except Exception as e:
            logger.error(f"Path normalization error: {e}")
            return None, None

        if os.path.commonpath(["/dev", device_path]) != "/dev":
            logger.error(f"Invalid device path (must be in /dev): {device_path}")
            return None, None

        allowed_mount_base = os.path.normpath("/mnt/usb")
        try:
            if os.path.commonpath([allowed_mount_base, normalized_mount]) != allowed_mount_base:
                logger.error(f"Invalid mount point: {normalized_mount}. Must be within {allowed_mount_base}")
                return None, None

            if normalized_mount == allowed_mount_base:
                logger.error(f"Cannot mount directly on {allowed_mount_base}")
                return None, None
        except ValueError:
            logger.error(f"Invalid paths for commonpath: {allowed_mount_base}, {normalized_mount}")
            return None, None

        return device_path, normalized_mount

    @staticmethod
    def mount_volume(device_path, mount_point):
        """
        Mounts a USB device to a specific mount point with security flags.
        """
        device_path, mount_point = USBMountManager._validate_paths(device_path, mount_point)
        if not device_path or not mount_point:
            return False

        if not USBGuardManager.is_installed():
            logger.error("USBGuard is not installed. Refusing to mount for security reasons.")
            return False

        if not os.path.exists(mount_point):
            try:
                os.makedirs(mount_point, exist_ok=True)
            except OSError as e:
                logger.error(f"Failed to create mount point {mount_point}: {e}")
                return False

        # -o noexec: Do not allow direct execution of any binaries on the mounted filesystem.
        # -o nosuid: Do not allow set-user-identifier or set-group-identifier bits to take effect.
        # -o nodev: Do not interpret character or block special devices on the filesystem.
        mount_options = "noexec,nosuid,nodev"

        try:
            command = ["sudo", "mount", "-o", mount_options, device_path, mount_point]
            subprocess.run(command, check=True, capture_output=True, text=True)
            logger.info(f"Successfully mounted {device_path} to {mount_point} with security options.")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to mount {device_path} to {mount_point}: {e.stderr}")
            return False

    @staticmethod
    def unmount_volume(mount_point):
        """
        Unmounts a volume from a specific mount point.

        Args:
            mount_point (str): The directory to unmount.

        Returns:
            bool: True if successful, False otherwise.
        """
        try:
            subprocess.run(["sudo", "umount", mount_point], check=True, capture_output=True, text=True)
            logger.info(f"Successfully unmounted {mount_point}.")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to unmount {mount_point}: {e.stderr}")
            return False
