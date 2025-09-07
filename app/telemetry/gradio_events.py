# =========================================
# File: app/telemetry/gradio_events.py
# Purpose: Helper to attach EventBus to UI streams (optional)
# =========================================
from __future__ import annotations
from typing import Callable, Awaitable
from app.telemetry.events import EVENT_BUS, TelemetryEvent

# Example subscriber you can use from tests or custom UIs
async def subscribe(callback: Callable[[TelemetryEvent], Awaitable[None]]):
    EVENT_BUS.subscribe(callback)