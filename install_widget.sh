#!/bin/bash
# Install Academic Tasks Native Plasma 6 Widget

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WIDGET_DIR="$SCRIPT_DIR/plasma-widget"
CLI_PATH="$SCRIPT_DIR/src/cli.py"

echo "Installing Academic Tasks CLI bridge..."
chmod +x "$CLI_PATH"

echo "Installing Plasma Widget..."
# Remove old version if exists
kpackagetool6 -t Plasma/Applet --remove org.ramiro.academictasks 2>/dev/null

# Install new version
kpackagetool6 -t Plasma/Applet --install "$WIDGET_DIR"

echo "Restarting Plasma shell to load the new widget..."
if command -v plasmashell >/dev/null 2>&1; then
    plasmashell --replace &
    disown
fi

echo ""
echo "=========================================================="
echo "✓ Native Widget Installed Successfully!"
echo "=========================================================="
echo "You can now add it to your desktop:"
echo "1. Right-click on your desktop"
echo "2. Select 'Add Widgets...'"
echo "3. Search for 'Academic Tasks' and drag it to your screen"
echo "=========================================================="
