"""
Device Manager - Generate and persist unique device ID for WebSocket routing

CRITICAL: Device ID is required for WebSocket message routing from cloud backend.
Without device_id, cloud cannot route messages back to the correct local backend instance.

Author: AgentVerse Team
"""

import uuid
import json
from pathlib import Path
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class DeviceManager:
    """
    Manage device identification for local backend instance.

    Generates a unique device ID on first run and persists it to disk.
    This ID is used for:
    - WebSocket connection routing
    - Message distribution targeting
    - Session tracking
    - Analytics

    Example:
        device_mgr = DeviceManager(cache_dir="/home/user/.agentverse")
        device_id = device_mgr.get_device_id()

        # Device ID persists across restarts
        device_mgr2 = DeviceManager(cache_dir="/home/user/.agentverse")
        assert device_mgr2.get_device_id() == device_id
    """

    def __init__(self, cache_dir: str):
        """
        Initialize device manager.

        Args:
            cache_dir: Directory to store device ID file
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        self.device_file = self.cache_dir / "device.json"
        self._device_id: Optional[str] = None
        self._device_name: Optional[str] = None

    def get_device_id(self) -> str:
        """
        Get device ID (generates and persists if doesn't exist).

        Returns:
            Unique device ID (UUID format)
        """
        if self._device_id:
            return self._device_id

        # Try to load existing device ID
        if self.device_file.exists():
            try:
                with open(self.device_file, 'r') as f:
                    data = json.load(f)
                    self._device_id = data.get("device_id")
                    self._device_name = data.get("device_name")

                    if self._device_id:
                        logger.info(f"Loaded device ID: {self._device_id}")
                        return self._device_id
            except Exception as e:
                logger.warning(f"Failed to load device ID: {e}")

        # Generate new device ID
        self._device_id = str(uuid.uuid4())
        self._device_name = self._generate_device_name()

        # Persist to disk
        try:
            with open(self.device_file, 'w') as f:
                json.dump({
                    "device_id": self._device_id,
                    "device_name": self._device_name,
                    "created_at": self._get_timestamp()
                }, f, indent=2)

            logger.info(f"Generated new device ID: {self._device_id}")
        except Exception as e:
            logger.error(f"Failed to persist device ID: {e}")

        return self._device_id

    def get_device_name(self) -> str:
        """
        Get human-readable device name.

        Returns:
            Device name (e.g., "laptop-abc123")
        """
        if not self._device_name:
            self.get_device_id()  # Loads or generates both

        return self._device_name or "unknown-device"

    def _generate_device_name(self) -> str:
        """Generate human-readable device name"""
        import platform
        import socket

        try:
            hostname = socket.gethostname()
            system = platform.system().lower()

            # Shorten device ID for readability
            short_id = self._device_id[:8] if self._device_id else "unknown"

            return f"{hostname}-{system}-{short_id}"
        except Exception:
            return f"device-{self._device_id[:8]}" if self._device_id else "unknown-device"

    def _get_timestamp(self) -> str:
        """Get current timestamp in ISO format"""
        from datetime import datetime
        return datetime.utcnow().isoformat()

    def reset_device_id(self):
        """
        Reset device ID (generates new one).

        Use case: User wants to register as new device
        """
        if self.device_file.exists():
            self.device_file.unlink()

        self._device_id = None
        self._device_name = None

        logger.info("Device ID reset")

        # Generate new ID
        return self.get_device_id()


# ============================================================================
# SINGLETON INSTANCE
# ============================================================================

_device_manager: Optional[DeviceManager] = None


def get_device_manager() -> DeviceManager:
    """
    Get singleton device manager instance.

    Must be initialized first via initialize_device_manager().

    Example:
        device_mgr = get_device_manager()
        device_id = device_mgr.get_device_id()
    """
    global _device_manager
    if _device_manager is None:
        raise RuntimeError("Device manager not initialized. Call initialize_device_manager() first.")
    return _device_manager


def initialize_device_manager(cache_dir: str) -> DeviceManager:
    """
    Initialize singleton device manager instance.

    Called on startup with cache directory from settings.

    Args:
        cache_dir: Directory to store device ID file

    Example:
        device_mgr = initialize_device_manager("/home/user/.agentverse")
        device_id = device_mgr.get_device_id()
    """
    global _device_manager
    _device_manager = DeviceManager(cache_dir)
    logger.info(f"Device manager initialized: {_device_manager.get_device_id()}")
    return _device_manager
