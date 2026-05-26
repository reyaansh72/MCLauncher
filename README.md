# MCLauncher

A clean, minimalist, high-performance daily-driver Minecraft Launcher built with Python, PySide6, and Material UI. This project communicates directly with native system configurations, keeping runtime operations fast, resource-friendly, and completely free of bloat.

## 🛠️ Project Architecture

To maintain a lightweight and easily maintainable codebase, this repository strictly tracks only the **three crucial files** required to execute and run the launcher infrastructure:

* `app.py` — Core UI architecture, game instance deployment routines, and thread-safe process managers.
* `config.json` — Local user data, active authentication configurations, and runtime flags.
* `java_rules.txt` — Manifest parsing maps for version listings and distribution path logic.

---

## 🏗️ Development & Build Guide

Follow these steps to configure your local workspace environment on Arch Linux and compile the launcher into a zero-dependency standalone native executable binary.

### 1. Environment Initialization

Navigate into your project folder and ensure your files are in place:

```bash
cd MyFirstProjectNoAi/

Initialize your Python virtual environment and install the essential runtime frameworks:
Bash

# Set up an isolated workspace environment
python -m venv venv
source venv/bin/activate

# Install critical dependencies
pip install PySide6 qt-material requests platformdirs pyinstaller

2. Standalone Binary Compilation

To bundle all background modules, stylesheets, dynamic window graphics engine layouts, and network protocols into a single portable application executable file, run PyInstaller:
Bash

pyinstaller --onefile --windowed \
    --name="MCLauncher" \
    --collect-all "qt_material" \
    --collect-all "PySide6" \
    --hidden-import="requests" \
    --hidden-import="platformdirs.loaders" \
    app.py

3. Local Deployment & Execution

Once the build engine finishes processing, your portable standalone binary will be generated inside the newly created dist/ directory.

Because the launcher actively reads and writes user profile states dynamically at runtime, you must copy your configuration assets directly next to your executable:
Bash

# Navigate to deployment distribution folder
cd dist/

# Ensure your structure matches this arrangement exactly:
# dist/
# ├── MCLauncher        <-- Compiled Standalone Application
# ├── config.json       <-- User settings profiles
# └── java_rules.txt    <-- System platform rules

# Execute the native binary layout directly
./MCLauncher

🚀 GitHub Release Guidelines

When distributing compilation updates or transferring workspaces:

    Ensure your local .gitignore is active so internal compilation directories (build/, __pycache__/, .spec) are never committed to your upstream branch.

    Navigate to your GitHub repository dashboard, select Releases -> Draft a new release.

    Tag your release profile version (e.g., v1.0.0), attach a release summary title, and drag-and-drop your standalone dist/MCLauncher binary directly into the asset deployment tray!
