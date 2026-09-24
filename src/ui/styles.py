"""KDE Breeze-inspired stylesheet for the Academic Tasks widget.

Detects the current KDE color scheme (dark / light) via environment
variables and the Plasma configuration and returns appropriate QSS.
"""

from __future__ import annotations

import subprocess
from functools import lru_cache


@lru_cache(maxsize=1)
def _detect_dark_mode() -> bool:
    """Return True if the system is likely using a dark color scheme."""
    try:
        result = subprocess.run(
            ["kreadconfig6", "--group", "General", "--key", "ColorScheme"],
            capture_output=True, text=True, timeout=2,
        )
        scheme = result.stdout.strip().lower()
        if scheme:
            return "dark" in scheme
    except Exception:
        pass
    # Fallback: try kreadconfig5
    try:
        result = subprocess.run(
            ["kreadconfig5", "--group", "General", "--key", "ColorScheme"],
            capture_output=True, text=True, timeout=2,
        )
        scheme = result.stdout.strip().lower()
        if scheme:
            return "dark" in scheme
    except Exception:
        pass
    return True  # default to dark


def is_dark_mode() -> bool:
    return _detect_dark_mode()


# ── color palettes ───────────────────────────────────────────────────

class _Colors:
    """Color constants inspired by KDE Breeze."""

    class Dark:
        BG_PRIMARY = "#1e1e2e"
        BG_SECONDARY = "#282840"
        BG_TERTIARY = "#313150"
        BG_HOVER = "#3b3b5c"
        BG_INPUT = "#232338"
        SURFACE = "#2a2a45"
        BORDER = "#3e3e62"
        BORDER_FOCUS = "#7c6fea"

        TEXT_PRIMARY = "#e0dff4"
        TEXT_SECONDARY = "#a09fbd"
        TEXT_MUTED = "#6e6d8a"
        TEXT_PLACEHOLDER = "#5a5978"

        ACCENT = "#7c6fea"
        ACCENT_HOVER = "#9488f0"
        ACCENT_BG = "rgba(124, 111, 234, 0.12)"

        STATUS_NOT_STARTED = "#6e6d8a"
        STATUS_IN_PROGRESS = "#f5a623"
        STATUS_COMPLETED = "#4caf82"

        DANGER = "#e05572"
        DANGER_HOVER = "#e8738d"

        OVERDUE = "#e05572"
        DUE_SOON = "#f5a623"

        SCROLLBAR = "#3e3e62"
        SCROLLBAR_HOVER = "#5a5978"

        SHADOW = "rgba(0, 0, 0, 0.3)"

    class Light:
        BG_PRIMARY = "#f5f4fb"
        BG_SECONDARY = "#eceaf6"
        BG_TERTIARY = "#e3e1f0"
        BG_HOVER = "#dddbe8"
        BG_INPUT = "#ffffff"
        SURFACE = "#ffffff"
        BORDER = "#d5d3e3"
        BORDER_FOCUS = "#6c5ce7"

        TEXT_PRIMARY = "#2d2b42"
        TEXT_SECONDARY = "#5a5872"
        TEXT_MUTED = "#8a88a0"
        TEXT_PLACEHOLDER = "#a09fB5"

        ACCENT = "#6c5ce7"
        ACCENT_HOVER = "#7b6df0"
        ACCENT_BG = "rgba(108, 92, 231, 0.08)"

        STATUS_NOT_STARTED = "#8a88a0"
        STATUS_IN_PROGRESS = "#e59500"
        STATUS_COMPLETED = "#3d9970"

        DANGER = "#d04060"
        DANGER_HOVER = "#da5a76"

        OVERDUE = "#d04060"
        DUE_SOON = "#e59500"

        SCROLLBAR = "#d5d3e3"
        SCROLLBAR_HOVER = "#c0bed0"

        SHADOW = "rgba(0, 0, 0, 0.08)"


def _c():
    """Return the active color set."""
    return _Colors.Dark if is_dark_mode() else _Colors.Light


# ── stylesheet generator ────────────────────────────────────────────

def get_stylesheet() -> str:
    """Return the full application QSS."""
    c = _c()
    return f"""
    /* ── Global ──────────────────────────────────────────────── */
    QWidget {{
        font-family: 'Inter', 'Noto Sans', 'Segoe UI', sans-serif;
        font-size: 13px;
        color: {c.TEXT_PRIMARY};
        background-color: {c.BG_PRIMARY};
    }}

    /* ── Scroll area ─────────────────────────────────────────── */
    QScrollArea {{
        border: none;
        background: transparent;
    }}
    QScrollArea > QWidget > QWidget {{
        background: transparent;
    }}
    QScrollBar:vertical {{
        background: transparent;
        width: 8px;
        margin: 2px;
        border-radius: 4px;
    }}
    QScrollBar::handle:vertical {{
        background: {c.SCROLLBAR};
        min-height: 30px;
        border-radius: 4px;
    }}
    QScrollBar::handle:vertical:hover {{
        background: {c.SCROLLBAR_HOVER};
    }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
        height: 0;
    }}
    QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
        background: transparent;
    }}

    /* ── QPushButton ─────────────────────────────────────────── */
    QPushButton {{
        background: {c.BG_TERTIARY};
        color: {c.TEXT_PRIMARY};
        border: 1px solid {c.BORDER};
        border-radius: 6px;
        padding: 6px 14px;
        font-weight: 500;
    }}
    QPushButton:hover {{
        background: {c.BG_HOVER};
        border-color: {c.BORDER_FOCUS};
    }}
    QPushButton:pressed {{
        background: {c.BG_SECONDARY};
    }}
    QPushButton:focus {{
        border-color: {c.BORDER_FOCUS};
        outline: none;
    }}

    QPushButton#addTaskBtn {{
        background: {c.ACCENT};
        color: white;
        border: none;
        border-radius: 8px;
        padding: 8px 18px;
        font-size: 13px;
        font-weight: 600;
    }}
    QPushButton#addTaskBtn:hover {{
        background: {c.ACCENT_HOVER};
    }}

    QPushButton#dangerBtn {{
        background: transparent;
        color: {c.DANGER};
        border: 1px solid {c.DANGER};
    }}
    QPushButton#dangerBtn:hover {{
        background: {c.DANGER};
        color: white;
    }}

    QPushButton#flatBtn {{
        background: transparent;
        border: none;
        color: {c.TEXT_SECONDARY};
        padding: 4px 8px;
    }}
    QPushButton#flatBtn:hover {{
        color: {c.TEXT_PRIMARY};
        background: {c.BG_HOVER};
        border-radius: 4px;
    }}

    /* ── QLineEdit / QTextEdit ───────────────────────────────── */
    QLineEdit, QTextEdit {{
        background: {c.BG_INPUT};
        color: {c.TEXT_PRIMARY};
        border: 1px solid {c.BORDER};
        border-radius: 6px;
        padding: 7px 10px;
        selection-background-color: {c.ACCENT};
        selection-color: white;
    }}
    QLineEdit:focus, QTextEdit:focus {{
        border-color: {c.BORDER_FOCUS};
    }}
    QLineEdit::placeholder {{
        color: {c.TEXT_PLACEHOLDER};
    }}

    /* ── QComboBox ───────────────────────────────────────────── */
    QComboBox {{
        background: {c.BG_INPUT};
        color: {c.TEXT_PRIMARY};
        border: 1px solid {c.BORDER};
        border-radius: 6px;
        padding: 6px 10px;
        min-width: 100px;
    }}
    QComboBox:hover {{
        border-color: {c.BORDER_FOCUS};
    }}
    QComboBox::drop-down {{
        border: none;
        width: 24px;
    }}
    QComboBox::down-arrow {{
        image: none;
        border-left: 4px solid transparent;
        border-right: 4px solid transparent;
        border-top: 5px solid {c.TEXT_SECONDARY};
        margin-right: 8px;
    }}
    QComboBox QAbstractItemView {{
        background: {c.SURFACE};
        color: {c.TEXT_PRIMARY};
        border: 1px solid {c.BORDER};
        border-radius: 6px;
        padding: 4px;
        selection-background-color: {c.ACCENT_BG};
        selection-color: {c.ACCENT};
        outline: none;
    }}

    /* ── QDateEdit ───────────────────────────────────────────── */
    QDateEdit {{
        background: {c.BG_INPUT};
        color: {c.TEXT_PRIMARY};
        border: 1px solid {c.BORDER};
        border-radius: 6px;
        padding: 6px 10px;
    }}
    QDateEdit:focus {{
        border-color: {c.BORDER_FOCUS};
    }}
    QDateEdit::drop-down {{
        border: none;
        width: 24px;
    }}
    QDateEdit::down-arrow {{
        image: none;
        border-left: 4px solid transparent;
        border-right: 4px solid transparent;
        border-top: 5px solid {c.TEXT_SECONDARY};
        margin-right: 8px;
    }}

    /* ── QCheckBox ───────────────────────────────────────────── */
    QCheckBox {{
        spacing: 8px;
        color: {c.TEXT_PRIMARY};
    }}
    QCheckBox::indicator {{
        width: 18px;
        height: 18px;
        border: 2px solid {c.BORDER};
        border-radius: 4px;
        background: {c.BG_INPUT};
    }}
    QCheckBox::indicator:checked {{
        background: {c.ACCENT};
        border-color: {c.ACCENT};
    }}

    /* ── QLabel ──────────────────────────────────────────────── */
    QLabel {{
        background: transparent;
    }}
    QLabel#headerLabel {{
        font-size: 18px;
        font-weight: 700;
        color: {c.TEXT_PRIMARY};
    }}
    QLabel#sectionLabel {{
        font-size: 11px;
        font-weight: 700;
        letter-spacing: 1px;
        color: {c.TEXT_MUTED};
        padding: 12px 0 4px 0;
    }}
    QLabel#subjectLabel {{
        font-size: 11px;
        color: {c.TEXT_SECONDARY};
    }}
    QLabel#dueLabel {{
        font-size: 11px;
        color: {c.DUE_SOON};
        font-weight: 500;
    }}
    QLabel#overdueLabel {{
        font-size: 11px;
        color: {c.OVERDUE};
        font-weight: 600;
    }}
    QLabel#countLabel {{
        font-size: 11px;
        color: {c.TEXT_MUTED};
        font-weight: 400;
    }}

    /* ── QFrame separator ────────────────────────────────────── */
    QFrame#separator {{
        background: {c.BORDER};
        max-height: 1px;
        min-height: 1px;
    }}

    /* ── QDialog ─────────────────────────────────────────────── */
    QDialog {{
        background: {c.BG_PRIMARY};
    }}

    /* ── QGroupBox ───────────────────────────────────────────── */
    QGroupBox {{
        border: 1px solid {c.BORDER};
        border-radius: 8px;
        margin-top: 14px;
        padding: 16px 12px 8px 12px;
        font-weight: 600;
        color: {c.TEXT_SECONDARY};
    }}
    QGroupBox::title {{
        subcontrol-origin: margin;
        left: 12px;
        padding: 0 6px;
    }}

    /* ── QToolTip ─────────────────────────────────────────────── */
    QToolTip {{
        background: {c.SURFACE};
        color: {c.TEXT_PRIMARY};
        border: 1px solid {c.BORDER};
        border-radius: 4px;
        padding: 4px 8px;
    }}

    /* ── QMenu (context menus) ───────────────────────────────── */
    QMenu {{
        background: {c.SURFACE};
        color: {c.TEXT_PRIMARY};
        border: 1px solid {c.BORDER};
        border-radius: 8px;
        padding: 4px;
    }}
    QMenu::item {{
        padding: 6px 24px 6px 12px;
        border-radius: 4px;
    }}
    QMenu::item:selected {{
        background: {c.ACCENT_BG};
        color: {c.ACCENT};
    }}
    QMenu::separator {{
        height: 1px;
        background: {c.BORDER};
        margin: 4px 8px;
    }}

    /* ── Task item frame ─────────────────────────────────────── */
    QFrame#taskItem {{
        background: {c.SURFACE};
        border: 1px solid {c.BORDER};
        border-radius: 8px;
        padding: 0px;
    }}
    QFrame#taskItem:hover {{
        border-color: {c.BORDER_FOCUS};
        background: {c.BG_SECONDARY};
    }}

    QFrame#taskItemCompleted {{
        background: {c.BG_SECONDARY};
        border: 1px solid {c.BORDER};
        border-radius: 8px;
        padding: 0px;
    }}
    QFrame#taskItemCompleted:hover {{
        border-color: {c.BORDER_FOCUS};
    }}

    /* ── Subject tag ─────────────────────────────────────────── */
    QLabel#subjectTag {{
        background: {c.ACCENT_BG};
        color: {c.ACCENT};
        border-radius: 4px;
        padding: 2px 8px;
        font-size: 11px;
        font-weight: 500;
    }}

    /* ── Status indicator button ─────────────────────────────── */
    QPushButton#statusNotStarted {{
        background: transparent;
        border: 2px solid {c.STATUS_NOT_STARTED};
        border-radius: 11px;
        min-width: 22px;
        max-width: 22px;
        min-height: 22px;
        max-height: 22px;
        font-size: 14px;
        color: {c.STATUS_NOT_STARTED};
    }}
    QPushButton#statusNotStarted:hover {{
        border-color: {c.STATUS_IN_PROGRESS};
        color: {c.STATUS_IN_PROGRESS};
    }}

    QPushButton#statusInProgress {{
        background: transparent;
        border: 2px solid {c.STATUS_IN_PROGRESS};
        border-radius: 11px;
        min-width: 22px;
        max-width: 22px;
        min-height: 22px;
        max-height: 22px;
        font-size: 12px;
        color: {c.STATUS_IN_PROGRESS};
    }}
    QPushButton#statusInProgress:hover {{
        border-color: {c.STATUS_COMPLETED};
        color: {c.STATUS_COMPLETED};
    }}

    QPushButton#statusCompleted {{
        background: {c.STATUS_COMPLETED};
        border: 2px solid {c.STATUS_COMPLETED};
        border-radius: 11px;
        min-width: 22px;
        max-width: 22px;
        min-height: 22px;
        max-height: 22px;
        font-size: 13px;
        font-weight: 700;
        color: white;
    }}
    QPushButton#statusCompleted:hover {{
        background: {c.STATUS_NOT_STARTED};
        border-color: {c.STATUS_NOT_STARTED};
    }}

    /* ── Filter bar ──────────────────────────────────────────── */
    QFrame#filterBar {{
        background: {c.BG_SECONDARY};
        border: 1px solid {c.BORDER};
        border-radius: 8px;
        padding: 4px;
    }}

    /* ── Search box ──────────────────────────────────────────── */
    QLineEdit#searchBox {{
        background: {c.BG_INPUT};
        border: 1px solid {c.BORDER};
        border-radius: 8px;
        padding: 8px 12px 8px 32px;
        font-size: 13px;
    }}
    QLineEdit#searchBox:focus {{
        border-color: {c.BORDER_FOCUS};
    }}
    """


def get_status_color(status) -> str:
    """Return the accent color for a given TaskStatus."""
    from models.enums import TaskStatus
    c = _c()
    return {
        TaskStatus.NOT_STARTED: c.STATUS_NOT_STARTED,
        TaskStatus.IN_PROGRESS: c.STATUS_IN_PROGRESS,
        TaskStatus.COMPLETED: c.STATUS_COMPLETED,
    }.get(status, c.TEXT_MUTED)


def get_colors():
    """Return the active color palette."""
    return _c()
