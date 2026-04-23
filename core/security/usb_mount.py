import subprocess
import logging
import os

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
