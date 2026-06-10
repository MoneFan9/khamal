import subprocess
import logging
import os
import re
from pathlib import Path
from .usb_guard import USBGuardManager

logger = logging.getLogger(__name__)

class USBMountManager:
    """
    USBMountManager: Secure physical ingestion engine.

    Khamal allows deploying code from physical USB drives. This class implements
    strict security controls to prevent this "physical vector" from compromising the host.
    """

    @staticmethod
    def _validate_paths(device_path, mount_point) -> tuple[bool, str, str]:
        """
        Internal helper to validate and normalize device and mount paths.
        """
        try:
            # 1. Basic normalization
            device_path = os.path.normpath(device_path)
            if not os.path.isabs(mount_point):
                logger.error(f"Mount point must be absolute: {mount_point}")
                return False, device_path, mount_point

            normalized_mount = os.path.normpath(mount_point)
        except Exception as e:
            logger.error(f"Path normalization error: {e}")
            return False, device_path, mount_point

        if os.path.commonpath(["/dev", device_path]) != "/dev":
            logger.error(f"Invalid device path (must be in /dev): {device_path}")
            return False, device_path, normalized_mount

        allowed_mount_base = os.path.normpath("/mnt/usb")
        try:
            if os.path.commonpath([allowed_mount_base, normalized_mount]) != allowed_mount_base:
                logger.error(f"Invalid mount point: {normalized_mount}. Must be within {allowed_mount_base}")
                return False, device_path, normalized_mount

            if normalized_mount == allowed_mount_base:
                logger.error(f"Cannot mount directly on {allowed_mount_base}")
                return False, device_path, normalized_mount
        except ValueError:
            logger.error(f"Invalid paths for commonpath: {allowed_mount_base}, {normalized_mount}")
            return False, device_path, normalized_mount

        return True, device_path, normalized_mount

    @staticmethod
    def mount_volume(device_path, mount_point):
        """
        Mounts a USB device to a specific mount point with security flags.

        Args:
            device_path (str): The path to the device (e.g., /dev/sdb1)
            mount_point (str): The directory where the device should be mounted.

        Returns:
            bool: True if successful, False otherwise.
        """
        # --- Security Hardening Protocol ---
        # 1. Path Normalization & Validation
        is_valid, device_path, normalized_mount = USBMountManager._validate_paths(device_path, mount_point)
        if not is_valid:
            return False

        # 2. Verify device is a block device
        import stat
        try:
            if not stat.S_ISBLK(os.stat(device_path).st_mode):
                logger.error(f"Device {device_path} is not a block device.")
                return False
        except OSError:
            logger.error(f"Device {device_path} not found.")
            return False

        # 4. Integrate with USBGuard
        if not USBGuardManager.is_installed():
            logger.error("USBGuard is not installed. Refusing to mount for security reasons.")
            return False

        if not USBGuardManager.is_service_active():
            logger.error("USBGuard service is not active. Refusing to mount for security reasons.")
            return False

        # 6. Verify device authorization in USBGuard
        # We ensure that the device (or its parent block device) is explicitly allowed by USBGuard.
        devices = USBGuardManager.list_devices()
        if devices is None:
             logger.error("Failed to retrieve device list from USBGuard.")
             return False

        # Attempt to find an 'allow' rule for the device path or its parent
        # (e.g., if device_path is /dev/sdb1, we also check for /dev/sdb)
        parent_device = device_path.rstrip('0123456789')

        authorized = False
        # Use regex with word boundaries to avoid partial matches (e.g., /dev/sdb matching /dev/sdb1)
        # and ensure 'allow' is present in the line.
        # We use a negative lookahead to ensure the path is not just a prefix (e.g. /dev/sdb vs /dev/sdb1)
        path_pattern = re.compile(rf"\ballow\b.*({re.escape(device_path)}|{re.escape(parent_device)})(?![\w/])")

        logger.debug(f"Checking USBGuard authorization for {device_path} (parent: {parent_device})")
        for line in devices.splitlines():
            if path_pattern.search(line):
                authorized = True
                break

        if not authorized:
             logger.error(f"Device {device_path} is not authorized by USBGuard.")
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
