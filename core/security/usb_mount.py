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
        Uses os.path.realpath to resolve symlinks and prevent bypasses.
        """
        try:
            # Resolve symlinks and normalize
            device_path = os.path.realpath(device_path)
            if not os.path.isabs(mount_point):
                logger.error(f"Mount point must be absolute: {mount_point}")
                return False, device_path, mount_point

            normalized_mount = os.path.realpath(mount_point)
        except Exception as e:
            logger.error(f"Path normalization error: {e}")
            return False, device_path, mount_point

        if os.path.commonpath(["/dev", device_path]) != "/dev":
            logger.error(f"Invalid device path (must be in /dev): {device_path}")
            return False, device_path, normalized_mount

        allowed_mount_base = os.path.realpath("/mnt/usb")
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
        is_valid, device_path, mount_point = USBMountManager._validate_paths(device_path, mount_point)
        if not is_valid:
            return False

        # 4. Integrate with USBGuard
        if not USBGuardManager.is_installed():
            logger.error("USBGuard is not installed. Refusing to mount for security reasons.")
            return False

        if not USBGuardManager.is_service_active():
            logger.error("USBGuard service is not active. Refusing to mount for security reasons.")
            return False

        # 5. Verify it's a block device
        if not Path(device_path).is_block_device():
            logger.error(f"Device {device_path} is not a valid block device.")
            return False

        # 6. Verify device authorization in USBGuard
        # We ensure that the device is explicitly allowed by USBGuard using 'with-devpath'.
        devices = USBGuardManager.list_devices()
        if devices is None:
             logger.error("Failed to retrieve device list from USBGuard.")
             return False

        authorized = False
        # Improved regex to specifically match 'allow' rules with the correct 'with-devpath'
        # Example line: 1: allow id 1234:5678 ... with-devpath "/dev/sdb1"
        path_pattern = re.compile(rf"^\s*\d+:\s+allow\b.*with-devpath\s+\"{re.escape(device_path)}\"")

        logger.debug(f"Checking USBGuard authorization for {device_path}")
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

        # -o noexec: Blocks execution of binaries (essential against malware).
        # -o nosuid: Prevents privilege escalation via setuid/setgid bits.
        # -o nodev: Disables device files interpretation.
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
        """
        try:
            subprocess.run(["sudo", "umount", mount_point], check=True, capture_output=True, text=True)
            logger.info(f"Successfully unmounted {mount_point}.")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to unmount {mount_point}: {e.stderr}")
            return False
