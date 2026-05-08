import subprocess
import logging
import os
from .usb_guard import USBGuardManager

logger = logging.getLogger(__name__)

class USBMountManager:
    """
    USBMountManager: Secure physical ingestion engine.

    Khamal allows deploying code from physical USB drives. This class implements
    strict security controls to prevent this "physical vector" from compromising the host.
    """

    @staticmethod
    def _validate_paths(device_path, mount_point):
        """
        Validates that the device and mount paths are secure.
        """
        # --- Security Hardening Protocol ---
        # 1. Path Normalization: Prevent traversal attacks (e.g., ../../etc/passwd)
        try:
            device_path = os.path.normpath(device_path)
            if not os.path.isabs(mount_point):
                logger.error(f"Mount point must be absolute: {mount_point}")
                return None, None

            normalized_mount = os.path.normpath(mount_point)
        except Exception as e:
            logger.error(f"Path normalization error: {e}")
            return None, None

        # Validate device path (must be in /dev/)
        if os.path.commonpath(["/dev", device_path]) != "/dev":
            logger.error(f"Invalid device path (must be in /dev): {device_path}")
            return None, None

        # Validate mount point (must be strictly within /mnt/usb/)
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
        device_path, normalized_mount = USBMountManager._validate_paths(device_path, mount_point)
        if not device_path:
            return False

        if not USBGuardManager.is_installed():
            logger.error("USBGuard is not installed. Refusing to mount for security reasons.")
            return False

        if not os.path.exists(normalized_mount):
            try:
                os.makedirs(normalized_mount, exist_ok=True)
            except OSError as e:
                logger.error(f"Failed to create mount point {normalized_mount}: {e}")
                return False

        # -o noexec: Blocks execution of binaries (essential against malware).
        # -o nosuid: Prevents privilege escalation via setuid/setgid bits.
        # -o nodev: Disables device files interpretation.
        mount_options = "noexec,nosuid,nodev"

        try:
            command = ["sudo", "mount", "-o", mount_options, device_path, normalized_mount]
            subprocess.run(command, check=True, capture_output=True, text=True)
            logger.info(f"Successfully mounted {device_path} to {normalized_mount} with security options.")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to mount {device_path} to {normalized_mount}: {e.stderr}")
            return False

    @staticmethod
    def unmount_volume(mount_point):
        """
        Unmounts a volume from a specific mount point.
        """
        try:
            subprocess.run(["sudo", "umount", mount_point], check=True, capture_output=True, text=True)
            logger.info(f"Successfully unmounted {mount_point}.")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to unmount {mount_point}: {e.stderr}")
            return False
