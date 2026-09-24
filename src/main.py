#!/usr/bin/env python3
"""Academic Tasks – lightweight KDE task-management widget.

A simple, Google Tasks-inspired desktop application for managing
university coursework, practical assignments, and study tasks.
"""

from __future__ import annotations

import sys
import os
import signal
import fcntl

# Add src to path so modules resolve correctly
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from pathlib import Path

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QApplication
from PyQt6.QtDBus import QDBusConnection, QDBusInterface

from storage.database import Database
from services.task_service import TaskService
from ui.main_window import MainWindow

# Lock file path
_LOCK_DIR = Path(os.environ.get("XDG_RUNTIME_DIR", "/tmp"))
_LOCK_FILE = _LOCK_DIR / "academic-tasks.lock"
_DBUS_SERVICE = "org.ramiro.AcademicTasks"
_DBUS_PATH = "/MainWindow"
_DBUS_IFACE = "org.ramiro.AcademicTasks"


def _is_already_running() -> bool:
    """Try to activate an existing instance via D-Bus. Returns True if successful."""
    bus = QDBusConnection.sessionBus()
    if not bus.isConnected():
        return False

    iface = QDBusInterface(_DBUS_SERVICE, _DBUS_PATH, _DBUS_IFACE, bus)
    if iface.isValid():
        iface.call("raise_window")
        return True
    return False


def main() -> int:
    # High-DPI scaling (automatic in Qt6, but explicit for clarity)
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    app = QApplication(sys.argv)
    app.setApplicationName("Academic Tasks")
    app.setOrganizationName("AcademicTasks")
    app.setDesktopFileName("academic-tasks")

    # Check if another instance is already running
    if _is_already_running():
        print("Academic Tasks is already running. Bringing to front.")
        return 0

    # Acquire lock file (non-blocking)
    try:
        lock_fd = open(_LOCK_FILE, "w")
        fcntl.flock(lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        lock_fd.write(str(os.getpid()))
        lock_fd.flush()
    except (IOError, OSError):
        # Another instance has the lock
        print("Academic Tasks is already running (lockfile).")
        return 0

    # Prefer system theme
    app.setStyle("Fusion")

    # Icon
    icon = QIcon.fromTheme("view-task", QIcon.fromTheme("checkbox"))
    app.setWindowIcon(icon)

    # Initialize database and seed sample data
    db = Database()
    service = TaskService(db)
    service.seed_sample_data()

    # Launch
    window = MainWindow(service)

    # Register on D-Bus so other instances can activate us
    bus = QDBusConnection.sessionBus()
    if bus.isConnected():
        bus.registerService(_DBUS_SERVICE)
        bus.registerObject(_DBUS_PATH, _DBUS_IFACE, window,
                           QDBusConnection.RegisterOption.ExportAllSlots)

    window.show()

    # Allow clean Ctrl+C
    signal.signal(signal.SIGTERM, lambda *_: app.quit())
    signal.signal(signal.SIGINT, lambda *_: app.quit())

    code = app.exec()

    # Cleanup
    db.close()
    try:
        fcntl.flock(lock_fd, fcntl.LOCK_UN)
        lock_fd.close()
        _LOCK_FILE.unlink(missing_ok=True)
    except Exception:
        pass

    return code


if __name__ == "__main__":
    sys.exit(main())

