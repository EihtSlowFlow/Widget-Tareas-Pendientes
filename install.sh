#!/bin/bash
# Install Academic Tasks desktop entry for the current user.
# Run this script once to integrate with KDE Plasma.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DESKTOP_FILE="$SCRIPT_DIR/academic-tasks.desktop"
AUTOSTART_DIR="$HOME/.config/autostart"
APPLICATIONS_DIR="$HOME/.local/share/applications"

# Update Exec path in the desktop file
MAIN_PY="$SCRIPT_DIR/src/main.py"
sed -i "s|Exec=.*|Exec=python3 $MAIN_PY|" "$DESKTOP_FILE"

# Install to applications menu
mkdir -p "$APPLICATIONS_DIR"
cp "$DESKTOP_FILE" "$APPLICATIONS_DIR/academic-tasks.desktop"
echo "✓ Installed to application menu"

# Optional: autostart
if [ "$1" = "--autostart" ]; then
    mkdir -p "$AUTOSTART_DIR"
    cp "$DESKTOP_FILE" "$AUTOSTART_DIR/academic-tasks.desktop"
    echo "✓ Added to autostart"
fi

echo ""
echo "Academic Tasks is ready!"
echo "Launch it from your application menu or run:"
echo "  python3 $MAIN_PY"
