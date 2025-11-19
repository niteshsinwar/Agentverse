"""
Lightweight File Watcher for Hot-Reload of User Configurations

Watches user config files (settings.json, tools.json, mcp.json, agent_store/)
and automatically refreshes in-memory configurations WITHOUT server restart.

This is a minimal implementation using Python's built-in watchdog library.
"""

import time
import threading
from pathlib import Path
from typing import Callable, Dict, Set
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileModifiedEvent, FileCreatedEvent, DirModifiedEvent


class ConfigFileWatcher(FileSystemEventHandler):
    """
    Watches configuration files and triggers reload callbacks.

    Debounces multiple events to avoid excessive reloads during rapid file changes.
    """

    def __init__(self, reload_callbacks: Dict[str, Callable]):
        """
        Args:
            reload_callbacks: Dict mapping file patterns to reload functions
                Example: {
                    'settings.json': reload_settings_func,
                    'agent_store': reload_agents_func,
                    'tools.json': reload_tools_func,
                    'mcp.json': reload_mcp_func
                }
        """
        self.reload_callbacks = reload_callbacks
        self.pending_reloads: Set[str] = set()
        self.debounce_delay = 0.5  # seconds
        self.last_reload_time: Dict[str, float] = {}

    def on_modified(self, event):
        """Handle file modification events"""
        if event.is_directory:
            # Handle agent_store directory changes
            if 'agent_store' in str(event.src_path):
                self._queue_reload('agent_store')
        else:
            # Handle individual file changes
            file_path = Path(event.src_path)
            filename = file_path.name

            # Check if this file matches any watched patterns
            for pattern, callback in self.reload_callbacks.items():
                if pattern in str(file_path):
                    self._queue_reload(pattern)
                    break

    def on_created(self, event):
        """Handle file creation events (new agents, etc.)"""
        self.on_modified(event)  # Same logic as modification

    def _queue_reload(self, pattern: str):
        """Queue a reload with debouncing to avoid excessive reloads"""
        current_time = time.time()
        last_reload = self.last_reload_time.get(pattern, 0)

        # Only reload if enough time has passed since last reload
        if current_time - last_reload >= self.debounce_delay:
            self._execute_reload(pattern)
            self.last_reload_time[pattern] = current_time
        else:
            # Queue for later (debounce) using threading instead of asyncio
            # (watchdog runs in separate thread without event loop)
            if pattern not in self.pending_reloads:
                self.pending_reloads.add(pattern)
                # Schedule reload after debounce delay
                timer = threading.Timer(self.debounce_delay, self._delayed_reload, args=[pattern])
                timer.daemon = True  # Don't prevent program exit
                timer.start()

    def _delayed_reload(self, pattern: str):
        """Execute reload after debounce delay"""
        if pattern in self.pending_reloads:
            self.pending_reloads.remove(pattern)
            self._execute_reload(pattern)
            self.last_reload_time[pattern] = time.time()

    def _execute_reload(self, pattern: str):
        """Execute the reload callback for a specific pattern"""
        callback = self.reload_callbacks.get(pattern)
        if callback:
            try:
                print(f"🔄 Hot-reload triggered: {pattern}")
                callback()
                print(f"✅ Hot-reload complete: {pattern}")
            except Exception as e:
                print(f"❌ Hot-reload failed for {pattern}: {e}")


def start_config_watcher(config_dir: Path, reload_callbacks: Dict[str, Callable]) -> Observer:
    """
    Start watching configuration files for changes.

    Args:
        config_dir: Base directory to watch (usually project root)
        reload_callbacks: Dict of file patterns to reload functions

    Returns:
        Observer instance (keep reference to prevent garbage collection)

    Example:
        observer = start_config_watcher(
            Path("backend"),
            {
                'config/settings.json': orchestrator.reload_settings,
                'config/tools.json': orchestrator.reload_tools,
                'config/mcp.json': orchestrator.reload_mcp,
                'agent_store': orchestrator.refresh_agents
            }
        )
    """
    event_handler = ConfigFileWatcher(reload_callbacks)
    observer = Observer()

    # Watch config directory
    config_path = config_dir / "config"
    if config_path.exists():
        observer.schedule(event_handler, str(config_path), recursive=False)
        print(f"👀 Watching: {config_path}")

    # Watch agent_store directory
    agent_store_path = config_dir / "agent_store"
    if agent_store_path.exists():
        observer.schedule(event_handler, str(agent_store_path), recursive=True)
        print(f"👀 Watching: {agent_store_path}")

    observer.start()
    print("✅ Configuration file watcher started (hot-reload enabled)")

    return observer


def stop_config_watcher(observer: Observer):
    """Stop the configuration file watcher"""
    if observer:
        observer.stop()
        observer.join()
        print("🛑 Configuration file watcher stopped")
