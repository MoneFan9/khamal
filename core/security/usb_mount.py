import subprocess
import logging
import os
import re
from pathlib import Path
from .usb_guard import USBGuardManager

logger = logging.getLogger(__name__)

class USBMountManager:
    """
    Utility class to securely mount USB volumes.
    Forces noexec, nosuid, and nodev options to prevent malware execution.
    """

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
        # --- Security Validation ---
        # 1. Resolve and Normalize paths to prevent traversal and symlink bypasses
        try:
            device_path = os.path.normpath(device_path)
            # We don't use realpath on device_path as it might not exist yet or might be a symlink we want (like /dev/disk/by-id/...)
            # but we still want to ensure it's in /dev/

            if not os.path.isabs(mount_point):
                logger.error(f"Mount point must be absolute: {mount_point}")
                return False

            # mount_point might not exist, so we can't always use realpath on it directly if it doesn't exist.
            # But we can use realpath on the parent if it exists.
            normalized_mount = os.path.normpath(mount_point)
        except Exception as e:
            logger.error(f"Path normalization error: {e}")
            return False

        # 2. Validate device path (must be in /dev/)
        if os.path.commonpath(["/dev", device_path]) != "/dev":
            logger.error(f"Invalid device path (must be in /dev): {device_path}")
            return False

        # 3. Validate mount point (must be strictly within /mnt/usb/)
        allowed_mount_base = os.path.normpath("/mnt/usb")

        # Check if it's within allowed_mount_base using commonpath
        try:
            if os.path.commonpath([allowed_mount_base, normalized_mount]) != allowed_mount_base:
                logger.error(f"Invalid mount point: {normalized_mount}. Must be within {allowed_mount_base}")
                return False

            # Prevent mounting directly on the base
            if normalized_mount == allowed_mount_base:
                logger.error(f"Cannot mount directly on {allowed_mount_base}")
                return False
        except ValueError:
            logger.error(f"Invalid paths for commonpath: {allowed_mount_base}, {normalized_mount}")
            return False

        # 4. Validate that device_path is a block device
        try:
            if not Path(device_path).is_block_device():
                logger.error(f"Device path is not a block device: {device_path}")
                return False
        except Exception as e:
            logger.error(f"Error validating block device {device_path}: {e}")
            return False

        # 5. Integrate with USBGuard: Ensure USBGuard is installed and service is active
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
