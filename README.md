# Academic Tasks Widget

A native KDE Plasma 6 widget and desktop application for managing university coursework, practical assignments, and study tasks. Inspired by Google Tasks but built for the Linux desktop.

![Academic Tasks](https://img.shields.io/badge/Platform-KDE_Plasma_6-blue?style=flat-square)
![Python](https://img.shields.io/badge/Python-3.10+-green?style=flat-square)
![PyQt6](https://img.shields.io/badge/GUI-PyQt6-purple?style=flat-square)
![SQLite](https://img.shields.io/badge/Storage-SQLite-orange?style=flat-square)

## Features

- **Native Plasma 6 Widget** — Seamlessly integrates into your KDE desktop or panels.
- **Extended Desktop App** — Click the `↗` button in the widget to open the full PyQt6 application.
- **Single-Instance Design** — Never clutters your screen with duplicate windows, powered by DBus and file locks.
- **Task management** — Create, edit, complete, and delete academic tasks easily.
- **Subject association** — Group and color-code tasks by university subjects.
- **Status tracking** — Not started → In progress → Completed (click to cycle).
- **Persistent storage** — SQLite database automatically tracks changes in real-time.

## Installation

You need Python 3.10+, PyQt6, and KDE Plasma 6.

```bash
# Clone the repository
git clone https://github.com/EihtSlowFlow/Widget-fechas-linux.git
cd Widget-fechas-linux

# Install PyQt6 dependency (if not using system packages)
pip install PyQt6

# Install the Plasma widget and desktop integration
chmod +x install_widget.sh
./install_widget.sh
```

After installation, the widget will be available in your Plasma Widgets explorer. Right click your desktop -> Add Widgets... -> Search for **Academic Tasks**.

## Architecture

The project is split into three main components:
1. **Plasma Widget (`plasma-widget/`)**: A native QML Plasma 6 applet that sits on your desktop, running efficiently on the KDE shell.
2. **CLI Bridge (`src/cli.py`)**: A lightweight Python script that reads the database and communicates with the QML widget in real-time using Plasma's DataEngines.
3. **GUI App (`src/main.py`)**: A fully-featured PyQt6 application for deep task management, filtering, and editing.

```
├── plasma-widget/          # Native KDE Plasma 6 QML Widget
├── src/
│   ├── cli.py              # CLI bridge for QML DataEngine
│   ├── main.py             # Desktop App entry point
│   ├── models/             # Data models
│   ├── storage/            # SQLite database manager
│   ├── services/           # Business logic
│   └── ui/                 # PyQt6 components
├── install_widget.sh       # KDE Plasma installation script
└── README.md
```

## Storage

Data is stored locally using SQLite at `~/.local/share/academic-tasks/tasks.db`. Deleting a subject will safely prompt you if there are completed tasks, but warn you if there are incomplete tasks remaining.

## License

GPL-3.0 — See [LICENSE](LICENSE)
