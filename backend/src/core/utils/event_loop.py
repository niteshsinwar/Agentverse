"""
Cross-Platform Event Loop Management

WHY: Windows uses ProactorEventLoop, Mac uses SelectorEventLoop - need unified interface
WHAT: Manages event loops with platform-specific handling
HOW: Creates persistent background loop on Windows, standard loop on Mac
"""

import sys
import asyncio
import threading
from typing import Optional, Any, Coroutine
import logging

logger = logging.getLogger(__name__)


class CrossPlatformEventLoop:
    """
    Unified event loop manager for Windows/Mac compatibility.

    Windows: Uses persistent ProactorEventLoop in background thread
    Mac/Linux: Uses standard SelectorEventLoop
    """

    def __init__(self):
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._thread: Optional[threading.Thread] = None
        self._is_windows = sys.platform == 'win32'

        if self._is_windows:
            self._setup_windows_loop()
        else:
            self._setup_unix_loop()

        logger.info(f"Event loop initialized for {sys.platform}")

    def _setup_windows_loop(self):
        """
        Windows: Create persistent ProactorEventLoop in background thread.

        WHY: Windows ProactorEventLoop can close unexpectedly in main thread
        WHAT: Persistent background thread with dedicated event loop
        HOW: Threading.Event for synchronization
        """
        loop_ready = threading.Event()

        def run_loop():
            # CRITICAL: Must create ProactorEventLoop on Windows
            self._loop = asyncio.ProactorEventLoop()
            asyncio.set_event_loop(self._loop)
            loop_ready.set()
            self._loop.run_forever()

        self._thread = threading.Thread(target=run_loop, daemon=True, name="WindowsEventLoop")
        self._thread.start()
        loop_ready.wait(timeout=5.0)  # Wait for loop to be ready

        if not loop_ready.is_set():
            raise RuntimeError("Failed to start Windows event loop")

        logger.debug("Windows ProactorEventLoop started in background thread")

    def _setup_unix_loop(self):
        """
        Mac/Linux: Use standard SelectorEventLoop.

        WHY: Standard approach works well on Unix systems
        WHAT: Get or create event loop
        HOW: Try to get running loop, create new if needed
        """
        try:
            self._loop = asyncio.get_running_loop()
            logger.debug("Using existing event loop")
        except RuntimeError:
            self._loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self._loop)
            logger.debug("Created new SelectorEventLoop")

    def run_async(self, coro: Coroutine, timeout: float = 30.0) -> Any:
        """
        Run coroutine with platform-specific handling.

        WHY: Different execution strategies for Windows vs Unix
        WHAT: Execute coroutine and return result
        HOW: run_coroutine_threadsafe on Windows, normal execution on Unix

        Args:
            coro: Coroutine to execute
            timeout: Maximum execution time in seconds

        Returns:
            Result of coroutine execution

        Raises:
            TimeoutError: If execution exceeds timeout
            RuntimeError: If event loop is not available
        """
        if not self._loop:
            raise RuntimeError("Event loop not initialized")

        if self._is_windows:
            # Windows: Use run_coroutine_threadsafe
            import concurrent.futures
            future = asyncio.run_coroutine_threadsafe(coro, self._loop)
            try:
                return future.result(timeout=timeout)
            except concurrent.futures.TimeoutError:
                future.cancel()
                raise TimeoutError(f"Operation timed out after {timeout}s")
        else:
            # Mac/Linux: Check if in async context
            try:
                loop = asyncio.get_running_loop()
                # Already in async context, create task
                return asyncio.create_task(coro)
            except RuntimeError:
                # Not in async context, run until complete
                return self._loop.run_until_complete(
                    asyncio.wait_for(coro, timeout=timeout)
                )

    def shutdown(self):
        """
        Cleanup event loop.

        WHY: Proper resource cleanup
        WHAT: Stop loop and close threads
        HOW: Platform-specific shutdown procedures
        """
        if not self._loop:
            return

        try:
            if self._is_windows:
                # Windows: Stop background loop
                self._loop.call_soon_threadsafe(self._loop.stop)
                if self._thread:
                    self._thread.join(timeout=5.0)
                logger.debug("Windows event loop stopped")
            else:
                # Mac/Linux: Close loop if not running
                if not self._loop.is_running():
                    self._loop.close()
                logger.debug("Unix event loop closed")
        except Exception as e:
            logger.error(f"Error during event loop shutdown: {e}")
        finally:
            self._loop = None


# Global singleton instance
platform_loop = CrossPlatformEventLoop()
